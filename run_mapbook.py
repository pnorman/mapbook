# encoding: utf-8

'''
	This file is part of mapbook.

	mapbook is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	mapbook is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with Mapbook.  If not, see <http://www.gnu.org/licenses/>.

	Copyright 2012 Paul Norman
'''

from mapbook import *
import math
import argparse

	
def create_example(opts):
	# Build a list of pages to skip
	skippedmaps = []
	if opts.skip:
		for options in opts.skip:
			for numbers in options.split(','):
				skippedmaps.append(int(numbers))
	
	sheet = Sheet(opts.pagewidth, opts.pageheight, 15.)

	mapwidth = opts.width/opts.columns
	rows = int(math.ceil(opts.height/(mapwidth*sheet.ratio)))
	print 'rows={}, cols={}'.format(rows, opts.columns)
	bbox = Bbox(opts.startx, opts.starty, mapwidth, sheet.ratio, '4%')
	myarea = Area(Pagelist(rows, opts.columns, 1, skippedmaps, right=False), bbox, sheet, dpi=opts.dpi)
	
	attribtext = 'Copyright OpenStreetMap contributors, CC BY-SA\nmapbook software Copyright 2012 Paul Norman, GPL v3\n\nSee www.openstreetmap.org for more information'
	appearance = Appearance(	mapfile=opts.mapfile,
								sidetext=TextSettings((1., 1., 1.), 'PT Sans Bold', .4, (0., 0., 0.)), 
								overviewtext=TextSettings((.25, .25, .25), 'PT Sans', 3.0, (.5, .5, .5)), 
								header=TextSettings((0., 0., 0.), 'PT Sans Bold', .6, (0., 0., 0.)), 
								title=Text((0., 0., 0.), 'PT Sans', 48, (0., 0., 0.),opts.title),
								attribution=Text((0., 0., 0.),'PT Sans', 12, (0., 0., 0.), attribtext))
	
	mybook = Book(opts.outputfile,myarea,appearance)
	mybook.create_title()
	mybook.create_preface()
	mybook.create_maps()
	mybook.create_attribution()
	mybook._surface.finish()

if __name__ == "__main__":
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
	parser.add_argument('--width', type=float, help='Width in mercator km of the overall map',required=True)
	parser.add_argument('--height', type=float, help='Target height in mercator km of the overall map',required=True)
	parser.add_argument('--columns',type=int,help='Number of columns of maps', default=4)
	
	# Page layout options
	parser.add_argument('--pagewidth', type=float, help='Page width in points. Should be <= physical page width. Default is 8.5x11 portrait.',default=612.)
	parser.add_argument('--pageheight', type=float, help='Page height in points. Should be <= physical page height. Default is 8.5x11 portrait.',default=792)

	parser.add_argument('--title', help='Title of the map',default='A mapbook map')

	# File options
	parser.add_argument('--mapfile',help='Mapnik XML file',default='osm.xml')
	parser.add_argument('--outputfile',help='Name of PDF file to create',default='map.pdf')
	
	# Grid options
	parser.add_argument('--skip',action='append',help='Comma-seperated list of map numbers to skip. May be specified multiple times', default='')
	
	# Page options
	parser.add_argument('--dpi',type=float,help='DPI of mapnik image', default=300.)
	opts=parser.parse_args()
	create_example(opts)
