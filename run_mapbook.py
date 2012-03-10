# encoding: utf-8
from mapbook import *

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
	parser.add_argument('--rows',type=int,help='Number of rows of maps', default=1)
	parser.add_argument('--columns',type=int,help='Number of columns of maps', default=1)
	parser.add_argument('--firstmap',type=int,help='Number of first map', default=1)
	parser.add_argument('--skip',action='append',help='Comma-seperated list of map numbers to skip. May be specified multiple times')
	
	# Page options
	parser.add_argument('--firstpage',type=int,help='Page number of first page', default=1)
	parser.add_argument('--blankfirst',action='store_true',help='Insert an empty page at the beginning of the PDF',default=False)
	parser.add_argument('--dpi',type=float,help='DPI of mapnik image', default=300.)
	
	opts=parser.parse_args()
	
	print opts
	
	# Build a list of pages to skip
	skippedmaps = []
	if opts.skip:
		for options in opts.skip:
			for numbers in options.split(','):
				skippedmaps.append(int(numbers))
		
	sheet = Sheet(opts.pagewidth, opts.pageheight, opts.pagepadding)
	bbox = Bbox(opts.startx, opts.starty, opts.width, sheet.ratio, opts.overwidth) 
	myarea = Area(Pagelist(opts.rows, opts.columns, opts.firstpage, skippedmaps, right=False), bbox, sheet, dpi=opts.dpi)
	appearance = Appearance(opts.mapfile,
	TextSettings((1., 1., 1.), 'PT Sans', .4, (0., 0., 0.)), 
	TextSettings((.25, .25, .25), 'PT Sans', 3.0, (.5, .5, .5)), 
	TextSettings((0., 0., 0.), 'PT Sans', .6, (0., 0., 0.)), 
	Text((0., 0., 0.), 'PT Sans', 1, (0., 0., 0.),'Vancouver'))
	
	mybook = Book(opts.outputfile,myarea,appearance)
	mybook.create_title()
	mybook.create_preface()
	mybook.create_maps()
	mybook.create_attribution()
	mybook.insert_blank_page()
	mybook.insert_blank_page()
	mybook._surface.finish()
	