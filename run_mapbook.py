#!/usr/bin/env python


class Page:
	def __init__(self, mapnumber, minx, miny, width, ratio):
		#bounds = (opts.startx, opts.starty, opts.startx+opts.width, opts.starty+opts.width*(opts.pageheight/opts.pagewidth))
	
		self.bounds=(minx, miny, minx+width, miny+width*ratio)

		self.mapnumber=mapnumber

		
		# Adjacent pages in the grid
		# ul uc ur
		# ml mc mr
		# dl dc dr

		self.ul = None
		self.uc = None
		self.ur = None
		self.ml = None
		self.mr = None
		self.dl = None
		self.dc = None
		self.dr = None

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
	parser.add_argument('--pagewidth', type=float, help='Page width in points. Should be <= physical page width',required=True)
	parser.add_argument('--pageheight', type=float, help='Page height in points. Should be <= physical page height',required=True)
	
	# File options
	parser.add_argument('--mapfile',help='Mapnik XML file',default='osm.xml')
	parser.add_argument('--outputfile',type=argparse.FileType('w'),help='Name of PDF file to create',default='map.pdf')
	
	# Grid options
	parser.add_argument('--rows',type=int,help='Number of rows of map pages', default=1)
	parser.add_argument('--columns',type=int,help='Number of columns of map pages', default=1)
	parser.add_argument('--firstmap',type=int,help='Number of first map', default=1)

	# Page options
	parser.add_argument('--firstpage',type=int,help='Page number of first page', default=1)
	
	opts=parser.parse_args()

	print opts
	
	import mapnik2 as mapnik
	import cairo
	
	# Initial mapnik setup
	merc = mapnik.Projection('+init=epsg:3857')
	m = mapnik.Map(int(opts.pagewidth),int(opts.pageheight))
	m.srs = merc.params()
	
	# Calculate some information
	padding=10
	mapwidth=opts.pagewidth-2*padding
	mapheight=opts.pageheight-2*padding
	
	
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
			print 'pagegrid[{}][{}]={} and should be {}'.format(y,x,pagegrid[y][x], n)
			thispage = Page(n,opts.startx+x*opts.width, opts.starty+y*opts.width*(mapheight/mapwidth),opts.width,(mapheight/mapwidth))
		
			
			if y+1<len(pagegrid):
				if x-1>=0:
					thispage.ul=pagegrid[y+1][x-1]
				thispage.uc=pagegrid[y+1][x]
				if x+1<len(pagegrid[y+1]):
					thispage.ur=pagegrid[y+1][x+1]
				
			if x-1>=0:
				thispage.ml=pagegrid[y][x-1]

			if x+1<len(pagegrid[y]):
				thispage.mr=pagegrid[y][x+1]
				
			if y-1>=0:
				if x-1>=0:
					thispage.dl=pagegrid[y-1][x-1]
				thispage.dc=pagegrid[y-1][x]
				if x+1<len(pagegrid[y-1]):
					thispage.dr=pagegrid[y-1][x+1]
				
				
			pages.append(thispage)
			
			
#	pages.append(Page(1,opts.startx+opts.width, opts.starty,opts.width,(mapheight/mapwidth)))
	
	# Start rendering pages
	print 'Rendering a total of {} pages'.format(opts.rows*opts.columns)
	
	book = cairo.PDFSurface(opts.outputfile,opts.pagewidth,opts.pageheight)
	#pages[0].bounds[0] - overwidth - 0.5 (mwidth-width)
	# = ............                   (opts.pagewidth/mapwidth-1)*width
	# minx, miny, maxx, maxy
	
	pagecount = opts.firstpage
	for page in pages:
	
		print 'Rendering map {} on page {}'.format(page.mapnumber, pagecount)
		bbox = (\
		page.bounds[0] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[2] - pages[0].bounds[0]),\
		page.bounds[1] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[3] - pages[0].bounds[1]),\
		page.bounds[2] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[2] - pages[0].bounds[0]),\
		page.bounds[1] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (pages[0].bounds[3] - pages[0].bounds[1])\
		)

		m.zoom_to_box(mapnik.Box2d(*bbox))
	
		mapnik.load_map(m,opts.mapfile)
	
		
	
		cr = cairo.Context(book)
		
		# Save the current clip region
		cr.save()
		
		cr.rectangle(padding,padding,mapwidth,mapheight)
		cr.clip()	
		
		mapnik.render(m,cr,0,0)
	
	# Restore the clip region
		cr.restore()
		
		cr.set_line_width(.25)
		cr.set_source_rgb(0, 0, 0)
		cr.rectangle(padding,padding,mapwidth,mapheight)
		cr.stroke()
		
		cr.show_page()
		pagecount = pagecount + 1

	
	book.finish()

	