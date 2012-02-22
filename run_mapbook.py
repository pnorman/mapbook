#!/usr/bin/env python


class Page:
	def __init__(self, mapnumber, minx, miny, width, ratio):
		#bounds = (opts.startx, opts.starty, opts.startx+opts.width, opts.starty+opts.width*(opts.pageheight/opts.pagewidth))
	
		self.bounds=(minx, miny, minx+width, miny+width*ratio)

		self.mapnumber=mapnumber

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
	
	parser.add_argument('--startx', type=float, help='West coordinate to map in mercator km',required=True)
	parser.add_argument('--starty', type=float, help='South coordinate to map in mercator km',required=True)
	parser.add_argument('--width', type=float, help='Width in mercator km of a map page',required=True)
	parser.add_argument('--overwidth', type=float, help='Width in mercator km to add to each side', default=0.)
	parser.add_argument('--pagewidth', type=float, help='Page width in points. Should be <= physical page width',required=True)
	parser.add_argument('--pageheight', type=float, help='Page height in points. Should be <= physical page height',required=True)
	parser.add_argument('--mapfile',help='Mapnik XML file')
	opts=parser.parse_args()

	print opts
	
	import mapnik2 as mapnik
	import cairo
	
	merc = mapnik.Projection('+init=epsg:3857')
	
	padding=10.
	mapwidth=opts.pagewidth-2*padding
	mapheight=opts.pageheight-2*padding
	
	# minx, miny, maxx, maxy
	bounds = (opts.startx, opts.starty, opts.startx+opts.width, opts.starty+opts.width*(opts.pageheight/opts.pagewidth))
	pages = []
	
	pages.append(Page(1,opts.startx, opts.starty,opts.width,(opts.pageheight/opts.pagewidth)))
	
	
	m = mapnik.Map(int(opts.pagewidth),int(opts.pageheight))
	m.srs = merc.params()
		
	m.zoom_to_box(mapnik.Box2d(*bounds))
	
	mapnik.load_map(m,opts.mapfile)
	
	book = cairo.PDFSurface("test.pdf",opts.pagewidth,opts.pageheight)

	
	cr = cairo.Context(book)
	
	# Save the current clip region
	cr.save()
	
	cr.rectangle(10,10,mapwidth,mapheight)
	cr.clip()	
	
	mapnik.render(m,cr,0,0)
	
	# Restore the clip region
	cr.restore()
	
	cr.set_line_width(.25)
	cr.set_source_rgb(0, 0, 0)
	cr.rectangle(10,10,mapwidth,mapheight)
	cr.stroke()

	
	book.finish()

	