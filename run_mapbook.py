#!/usr/bin/python


class Page:
	def __init__(self, surface, mapnumber):
		self.surface=surface
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
	
	parser.add_argument('--startx', type=float, help='West coordinate to map in mercator km')
	parser.add_argument('--starty', type=float, help='South coordinate to map in mercator km')
	parser.add_argument('--width', type=float, help='Width in mercator km of a map page')
	parser.add_argument('--overwidth', type=float, help='Width in mercator km to add to each side')
	parser.add_argument('--pagewidth', type=float, help='Page width in points. Should be <= physical page width',required=True)
	parser.add_argument('--pageheight', type=float, help='Page height in points. Should be <= physical page height',required=True)
	opts=parser.parse_args()

	print opts
		
	import mapnik2 as mapnik
	import cairo
	
	padding=10
	mapwidth=opts.pagewidth-2*padding
	mapheight=opts.pageheight-2*padding
	
	surface = cairo.PDFSurface("test.pdf",opts.pagewidth,opts.pageheight)
	book = Page(cairo.PDFSurface("test.pdf",opts.pagewidth,opts.pageheight),0)
	
	cr = cairo.Context(book.surface)
	
	cr.set_line_width(1)
	cr.set_source_rgb(0.22, 0.08, 0.69)
	cr.rectangle(10,10,mapwidth,mapheight)
	cr.stroke()
	
	 

	