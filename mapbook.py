#!/usr/bin/env python

class Page:
	def __init__(self, mapnumber, minx, miny, width, ratio):
	
		self.bounds=(minx, miny, minx+width, miny+width*ratio)

		self.mapnumber=mapnumber
		
		# Adjacent pages in the grid
		self.up = None
		self.left = None
		self.right = None
		self.down = None

if __name__ == "__main__":
	import argparse
	
	class LineArgumentParser(argparse.ArgumentParser):
		def convert_arg_line_to_args(self, arg_line):
			
			if arg_line:
				if arg_line.strip()[0] == '#':
					return
					
				for arg in ('--' + arg_line).split():
					if not arg.strip():
						continrue
					yield arg
 
	parser = LineArgumentParser(description='Create a mapbook',fromfile_prefix_chars='@')
	
	# Location-based options
	parser.add_argument('--startx', type=float, help='West coordinate to map in mercator km',required=True)
	parser.add_argument('--starty', type=float, help='South coordinate to map in mercator km',required=True)
	parser.add_argument('--width', type=float, help='Width in mercator km of a map page',required=True)
	parser.add_argument('--overwidth', type=float, help='Width in mercator km to add to each side', default=0.)
	
	# Page layout options
	parser.add_argument('--pagewidth', type=float, help='Page width in points. Should be <= physical page width',required=True)
	parser.add_argument('--pageheight', type=float, help='Page height in points. Should be <= physical page height',required=True)
	parser.add_argument('--pagepadding', type=float, help='Padding around the edges of each map',default=15.)

	# File options
	parser.add_argument('--mapfile',help='Mapnik XML file',default='osm.xml')
	parser.add_argument('--outputfile',help='Name of PDF file to create',default='map.pdf')
	
	# Grid options
	parser.add_argument('--rows',type=int,help='Number of rows of map pages', default=1)
	parser.add_argument('--columns',type=int,help='Number of columns of map pages', default=1)
	parser.add_argument('--firstmap',type=int,help='Number of first map', default=1)

	# Page options
	parser.add_argument('--firstpage',type=int,help='Page number of first page', default=1)
	parser.add_argument('--blankfirst',action='store_true',help='Insert an empty page at the beginning of the PDF',default=False)
	parser.add_argument('--dpi',type=float,help='DPI of mapnik image', default=300.)
	
	opts=parser.parse_args()
	
	import mapnik2 as mapnik
	import cairo
	import pango
	import pangocairo
	import tempfile
	
	# Initial mapnik setup
	merc = mapnik.Projection('+init=epsg:3857')
	m = mapnik.Map(int(opts.pagewidth*opts.dpi/72.0),int(opts.pageheight*opts.dpi/72.0))
	# Fixme: specify srs?
	m.srs = merc.params()
	
	im = mapnik.Image(int(opts.pagewidth*opts.dpi/72.0),int(opts.pageheight*opts.dpi/72.0))
	
	# Calculate some information
	mapwidth=opts.pagewidth-opts.pagepadding
	mapheight=opts.pageheight-2*opts.pagepadding
	
	# Lay out the grid of pages
	# pagegrid
	# [2,0] [2,1] [2,2] [2,3]
	# [1,0] [1,1] [1,2] [1,3]
	# [0,0] [0,1] [0,2] [0,3]
	
	pagegrid = []
	for y in range(opts.rows):
		pagegrid.append(range(opts.firstmap+y*opts.columns,opts.firstmap+(1+y)*opts.columns))
	
	
	# Define the pages
	pages = []
	
	for y, row in enumerate(pagegrid):
		for x, n in enumerate(row):
			thispage = Page(n,opts.startx+x*opts.width, opts.starty+y*opts.width*(mapheight/mapwidth),opts.width,(mapheight/mapwidth))
		
			if y+1<len(pagegrid):
				thispage.uc=pagegrid[y+1][x]

			if x-1>=0:
				thispage.ml=pagegrid[y][x-1]

			if x+1<len(pagegrid[y]):
				thispage.mr=pagegrid[y][x+1]

			if y-1>=0:
				thispage.dc=pagegrid[y-1][x]

			pages.append(thispage)
		
	# Start rendering pages
	print 'Rendering a total of {} pages'.format(opts.rows*opts.columns)

	
	book = cairo.PDFSurface(opts.outputfile,opts.pagewidth,opts.pageheight)

	pagecount = opts.firstpage
	
	ctx = pangocairo.CairoContext(cairo.Context(book))
	
	if opts.blankfirst == True:
		print 'printing blank page'
		#ctx.show_page()
		#pagecount = pagecount + 1

	for page in pages:
	
		print 'Rendering map {} on page {}'.format(page.mapnumber, pagecount)
		
		#pages[0].bounds[0] - overwidth - 0.5 * (mwidth-width)
		# = . . .                             *(opts.pagewidth/mapwidth-1)*width
		# minx, miny, maxx, maxy

		bbox = (\
		page.bounds[0] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[2] - pages[0].bounds[0]),\
		page.bounds[1] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[3] - pages[0].bounds[1]),\
		page.bounds[2] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[2] - pages[0].bounds[0]),\
		page.bounds[1] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[3] - pages[0].bounds[1])\
		)

		m.zoom_to_box(mapnik.Box2d(*bbox))

		mapnik.load_map(m,opts.mapfile)
		mapnik.render(m,im,opts.dpi/90.7)
		imagefile=tempfile.NamedTemporaryFile(suffix='.png',delete=True)
		im.save(imagefile.name)
		imgs = cairo.ImageSurface.create_from_png(imagefile)

		# Save the current clip region
		ctx.save()
		# Save the current scale

		if pagecount % 2 != 1:
			ctx.rectangle(opts.pagepadding,opts.pagepadding,mapwidth,mapheight)
		else:
			ctx.rectangle(0,opts.pagepadding,mapwidth,mapheight)
		ctx.clip()

		ctx.scale(72/opts.dpi,72/opts.dpi)
		ctx.set_source_surface(imgs)
	
		ctx.paint()
		#mapnik.render(m,ctx,0,0)
	
	# Restore the clip region
		ctx.restore()
		
		ctx.set_line_width(.25)
		ctx.set_source_rgb(0, 0, 0)
		if pagecount % 2 != 1:
			ctx.rectangle(opts.pagepadding,opts.pagepadding,mapwidth,mapheight)
		else:
			ctx.rectangle(0,opts.pagepadding,mapwidth,mapheight)
		ctx.stroke()
		
		
		
		# Draw adjacent page arrows
		ctx.set_source_rgb(0., 0., 0.)
		if pagecount % 2 != 1:
			if page.left:
				ctx.move_to(0,opts.pageheight/2)
				ctx.rel_line_to(opts.pagepadding,-opts.pagepadding)
				ctx.rel_line_to(0,2*opts.pagepadding)
				ctx.close_path()
		else:
			if page.right:
				ctx.move_to(opts.pagewidth, opts.pageheight/2)
				ctx.rel_line_to(-opts.pagepadding,opts.pagepadding)
				ctx.rel_line_to(0,-2*opts.pagepadding)
				ctx.close_path()
		if page.up:
			ctx.move_to(opts.pagewidth/2,0.)
			ctx.rel_line_to(opts.pagepadding,opts.pagepadding)
			ctx.rel_line_to(-2*opts.pagepadding,0)
			ctx.close_path()
		if page.down:
			ctx.move_to(opts.pagewidth/2,opts.pageheight)
			ctx.rel_line_to(opts.pagepadding,-opts.pagepadding)
			ctx.rel_line_to(-2*opts.pagepadding,0)
			ctx.close_path()

		ctx.fill()
		
		# Draw adjacent page numbers
		ctx.set_source_rgb(1., 1., 1.)		
		arrowfont = pango.FontDescription("Sans " + str(opts.pagepadding*.38))
		
		if pagecount % 2 != 1:
			if page.right:
				layout=ctx.create_layout()
				layout.set_width(int(opts.pagepadding*2))
				layout.set_alignment(pango.ALIGN_CENTER)
				layout.set_font_description(arrowfont)
				layout.set_text(str(page.right))
				ctx.move_to(opts.pagewidth-opts.pagepadding*2/3, opts.pageheight/2-0.5*layout.get_size()[1]/pango.SCALE)
				ctx.update_layout(layout)
				ctx.show_layout(layout)

		else:
			if page.left:
				layout=ctx.create_layout()
				layout.set_width(int(opts.pagepadding*2))
				layout.set_alignment(pango.ALIGN_CENTER)
				layout.set_font_description(arrowfont)
				layout.set_text(str(page.left))
				ctx.move_to(opts.pagepadding*2/3, opts.pageheight/2-0.5*layout.get_size()[1]/pango.SCALE)
				ctx.update_layout(layout)
				ctx.show_layout(layout)

		if page.up:
			layout=ctx.create_layout()
			layout.set_width(int(opts.pagepadding*2))
			layout.set_alignment(pango.ALIGN_CENTER)
			layout.set_font_description(arrowfont)
			layout.set_text(str(page.up))
			ctx.move_to(opts.pagewidth/2, opts.pagepadding*2/3-0.5*layout.get_size()[1]/pango.SCALE)
			ctx.update_layout(layout)
			ctx.show_layout(layout)		
		
		if page.down:
			layout=ctx.create_layout()
			layout.set_width(int(opts.pagepadding*2))
			layout.set_alignment(pango.ALIGN_CENTER)
			layout.set_font_description(arrowfont)
			layout.set_text(str(page.down))
			ctx.move_to(opts.pagewidth/2, opts.pageheight-opts.pagepadding*2/3-0.5*layout.get_size()[1]/pango.SCALE)
			ctx.update_layout(layout)
			ctx.show_layout(layout)
		
		# Draw mapnumber text
		if pagecount % 2 != 1: 
			ctx.rectangle(0.,opts.pageheight-opts.pagepadding, opts.pagepadding*2, opts.pagepadding)
		else:
			ctx.rectangle(opts.pagewidth-opts.pagepadding*2,opts.pageheight-opts.pagepadding, opts.pagepadding*2, opts.pagepadding)
			
		ctx.set_source_rgb(0., 0., 0.)
		ctx.fill()

		ctx.set_source_rgb(1., 1., 1.)
		layout=ctx.create_layout()
		layout.set_width(int(opts.pagepadding*4))
		if pagecount % 2 != 1: 
			layout.set_alignment(pango.ALIGN_LEFT)
		else:
			layout.set_alignment(pango.ALIGN_RIGHT)
			
		layout.set_font_description(pango.FontDescription("Sans " + str(opts.pagepadding*.5)))
		layout.set_text(str(page.mapnumber))
		if pagecount % 2 != 1: 		
			ctx.move_to(opts.pagepadding,opts.pageheight-opts.pagepadding)
		else:
			ctx.move_to(opts.pagewidth-opts.pagepadding,opts.pageheight-opts.pagepadding)
		
		ctx.update_layout(layout)
		ctx.show_layout(layout)

		# Move to the next page
		ctx.show_page()
		pagecount = pagecount + 1

	book.finish()

	