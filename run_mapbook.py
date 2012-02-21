#!/usr/bin/python

if __name__ == "__main__":
	import argparse
	
	class LineArgumentParser(argparse.ArgumentParser):
		def convert_arg_line_to_args(self, arg_line):
		
			if arg_line.strip()[0] == '#':
				return
				
			for arg in ('--' + arg_line).split():
				if not arg.strip():
					continue
				yield arg
 
	parser = LineArgumentParser(description='Create a mapbook',fromfile_prefix_chars='@')
	
	parser.add_argument('--startx', type=float, help='West coordinate to map in mercator km')
	parser.add_argument('--starty', type=float, help='South coordinate to map in mercator km')
	parser.add_argument('--width', type=float, help='Width in mercator km of a map page')
	parser.add_argument('--overwidth', type=float, help='Width in mercator km to add to each side')
	
	print parser.parse_args()


	import mapnik2 as mapnik
	import cairo