#!/usr/bin/env python

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

import mapnik2 as mapnik

import cairo
import pango
import pangocairo
import tempfile
import types

POINTS_PER_INCH = 72.0
BASE_PPI = 90.7

class Book:
	def __init__(self, fobj, area, mapfile, font = 'Sans'):

		# Setup cairo
		self.area = area
		self.mapfile = mapfile
		self._surface=cairo.PDFSurface(fobj,*(self.area.pagesize_points))
		self._ctx = cairo.Context(self._surface)
		self.font = font
		
		# Setup mapnik
		self._m=mapnik.Map(*(self.area.map_size))
		self._m.aspect_fix_mode=mapnik.aspect_fix_mode.GROW_BBOX
		self._im=mapnik.Image(*(self.area.pagesize_pixels))
		mapnik.load_map(self._m,mapfile) # Fixme: specify srs?		
				
	
	def create_preface(self):
		self._render_map(Page(None, None, None, False), self.area.left_extent())
		self._ctx.show_page()
		self._render_map(Page(None, None, None, True), self.area.right_extent())
		self._ctx.show_page()
		
	def create_index(self):
		pass
	
	def create_maps(self):
		for page in self.area.pagelist:
			print "Rendering page {}".format(page.number)
			self._render_page(page)
			
	def _render_page(self, page):
		self._render_map(page, self.area.full_bounds(page))
		
		self._ctx.set_line_width(.4)
		self._ctx.set_source_rgb(0, 0, 0)
		self.area.sheet.draw_inset(self._ctx,page)
		self._ctx.stroke()
		
		self._ctx.set_source_rgb(0., 0., 0.)
		self._render_arrow_path(page)
		self._ctx.fill()
		
		self._ctx.set_source_rgb(1., 1., 1.)
		self._ctx.select_font_face(self.font)
		self._ctx.set_font_size(opts.pagepadding*.4)
		self._render_arrow_text(page)
		self._ctx.stroke()
		
		self._ctx.set_source_rgb(0., 0., 0.)
		self._render_number_path(page)
		self._ctx.fill()
		
		self._ctx.set_source_rgb(1., 1., 1.)
		self._ctx.select_font_face(self.font)
		self._ctx.set_font_size(opts.pagepadding*.8)
		self._render_number_text(page)
		self._ctx.stroke()
		
		self._ctx.show_page()

	def _render_map(self, page, bbox):
		print bbox
		self._m.zoom_to_box(bbox)
		mapnik.render(self._m,self._im,self.area.scale)
		imagefile=tempfile.NamedTemporaryFile(suffix='.png',delete=True)
		self._im.save(imagefile.name)
		
		# Set up the cairo ImageSurface
		imgsurface = cairo.ImageSurface.create_from_png(imagefile)

		self._ctx.save()
		self.area.sheet.draw_inset(self._ctx,page)
		self._ctx.clip()
		self._ctx.scale(POINTS_PER_INCH/self.area.dpi,POINTS_PER_INCH/self.area.dpi)
		self._ctx.set_source_surface(imgsurface)
		self._ctx.paint()
		self._ctx.restore()
		
	def _render_arrow_path(self, page):
		'''
		Creates the sub-paths for the page arrows
		'''
		if self.area.pagelist.number(page.x, page.y+1):
			# Top arrow
			self._ctx.move_to(self.area.sheet.page_inset(page)[0]+self.area.sheet.page_inset(page)[2]/2, 0)
			self._ctx.rel_line_to(self.area.sheet.padding,self.area.sheet.padding)
			self._ctx.rel_line_to(-2*self.area.sheet.padding,0)
			self._ctx.close_path()

		if self.area.pagelist.number(page.x, page.y-1):
			# Bottom arrow
			self._ctx.move_to(self.area.sheet.page_inset(page)[0]+self.area.sheet.page_inset(page)[2]/2, self.area.sheet.pageheight)
			self._ctx.rel_line_to(self.area.sheet.padding,-self.area.sheet.padding)
			self._ctx.rel_line_to(-2*self.area.sheet.padding,0)
			self._ctx.close_path()
		
		if page.right:
			if self.area.pagelist.number(page.x+1, page.y):
				# Right arrow
				self._ctx.move_to(self.area.sheet.pagewidth,float(self.area.sheet.pageheight)/2)
				self._ctx.rel_line_to(-self.area.sheet.padding,self.area.sheet.padding)
				self._ctx.rel_line_to(0,-2*self.area.sheet.padding)
				self._ctx.close_path()
				
		else:
			if self.area.pagelist.number(page.x-1, page.y):
				# Left arrow
				self._ctx.move_to(0,float(self.area.sheet.pageheight)/2)
				self._ctx.rel_line_to(self.area.sheet.padding,self.area.sheet.padding)
				self._ctx.rel_line_to(0,-2*self.area.sheet.padding)
				self._ctx.close_path()

	def _render_arrow_text(self, page):
		if self.area.pagelist.number(page.x, page.y+1):
			# Top text
			self._ctx.move_to(self.area.sheet.page_inset(page)[0]+self.area.sheet.page_inset(page)[2]/2, 0.6667*self.area.sheet.padding)
			print_centered_text(self._ctx, str(self.area.pagelist.number(page.x, page.y+1)))
			
		if self.area.pagelist.number(page.x, page.y-1):
			# Bottom text
			self._ctx.move_to(self.area.sheet.page_inset(page)[0]+self.area.sheet.page_inset(page)[2]/2, self.area.sheet.pageheight - 0.6667*self.area.sheet.padding)
			print_centered_text(self._ctx, str(self.area.pagelist.number(page.x, page.y-1)))
		
		if page.right:
			if self.area.pagelist.number(page.x+1, page.y):
				# Right text
				self._ctx.move_to(self.area.sheet.pagewidth-0.6667*self.area.sheet.padding,float(self.area.sheet.pageheight)/2)
				print_centered_text(self._ctx, str(self.area.pagelist.number(page.x+1, page.y)))

		else:
			if self.area.pagelist.number(page.x-1, page.y):
				# Left text
				self._ctx.move_to(0.6667*self.area.sheet.padding,float(self.area.sheet.pageheight)/2)
				print_centered_text(self._ctx, str(self.area.pagelist.number(page.x-1, page.y)))
	
	def _render_number_path(self, page):
		if page.right:
			self._ctx.rectangle(self.area.sheet.pagewidth, self.area.sheet.pageheight, -4*self.area.sheet.padding, -self.area.sheet.padding)
		else:
			self._ctx.rectangle(0, self.area.sheet.pageheight, 4*self.area.sheet.padding, -self.area.sheet.padding)
	
	def _render_number_text(self, page):
		if page.right:
			self._ctx.move_to(self.area.sheet.pagewidth-2*self.area.sheet.padding, self.area.sheet.pageheight-0.5*self.area.sheet.padding)
		else:
			self._ctx.move_to(2*self.area.sheet.padding, self.area.sheet.pageheight-0.5*self.area.sheet.padding)
		print_centered_text(self._ctx, str(page.number))
	
class Area:
	'''
	It is an error if bbox.ratio and sheet.ratio do not match
	'''
	
	def __init__(self, pagelist, bbox, sheet, dpi=300.):
		self.pagelist=pagelist
		self.bbox=bbox
		self.sheet=sheet
		self.dpi=dpi
		
	@property
	def map_size(self):
		return (int((self.sheet.pagewidth - self.sheet.padding)*self.dpi/POINTS_PER_INCH),
							int((self.sheet.pageheight - 2*self.sheet.padding)*self.dpi/POINTS_PER_INCH))
	
	@property	
	def pagesize_points(self):
		return (int(self.sheet.pagewidth), int(self.sheet.pageheight))
		
	@property	
	def pagesize_pixels(self):
		return (int(self.sheet.pagewidth*self.dpi/POINTS_PER_INCH), int(self.sheet.pageheight*self.dpi/POINTS_PER_INCH))
	
	@property
	def scale(self):
		return self.dpi/BASE_PPI
	
	def full_bounds(self,page):
		'''
		Returns the size of the bbox necessary to cover the full page and allow for padding
		'''
		y_avg = (self.bbox.bounds(page)[3]+self.bbox.bounds(page)[1])/2
		if page.right:
			return mapnik.Box2d(
									self.bbox.bounds(page)[0],
									(self.bbox.bounds(page)[1]-y_avg)*float(self.pagesize_pixels[1])/self.map_size[1]+y_avg,
									(self.bbox.bounds(page)[2]-self.bbox.bounds(page)[0])*float(self.pagesize_pixels[0])/self.map_size[0]+self.bbox.bounds(page)[0],
									(self.bbox.bounds(page)[3]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg)
		else:
			return mapnik.Box2d(
									(self.bbox.bounds(page)[0]-self.bbox.bounds(page)[2])*float(self.pagesize_pixels[0])/self.map_size[0]+self.bbox.bounds(page)[2],
									(self.bbox.bounds(page)[1]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg,
									self.bbox.bounds(page)[2],
									(self.bbox.bounds(page)[3]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg)
	
	@property
	def extent(self):
		'''
		Returns the bbox that encloses all pages printed, with no overwidth allowance
		'''
		min_x = min(page.x for page in self.pagelist)
		min_y = min(page.y for page in self.pagelist)
		max_x = max(page.x for page in self.pagelist)
		max_y = max(page.y for page in self.pagelist)
		
		print '(min_x,min_y,max_x,max_y)=({},{},{},{})'.format(min_x,min_y,max_x,max_y)
		return (self.bbox.startx+min(page.x for page in self.pagelist)*self.bbox.width,
				self.bbox.starty+min(page.y for page in self.pagelist)*self.bbox.width*self.bbox.ratio,
				self.bbox.startx+(max(page.x for page in self.pagelist)+1)*self.bbox.width,
				self.bbox.starty+(max(page.y for page in self.pagelist)+1)*self.bbox.width*self.bbox.ratio)
				
	def full_extent(self):
		'''
		Returns the bbox to display for the index maps, with no padding allowance
		'''
		extent = self.extent
		
		x_avg = (extent[0]+extent[2])/2
		y_avg = (extent[1]+extent[3])/2
		width = extent[2]-extent[0]
		height = extent[3]-extent[1]
		
		# The true ratio of the overview page is height/(2*width) since it is two pages wide
		scale = max((width/height)/self.bbox.ratio,self.bbox.ratio/(width/height))
		print 'scale=max({},{})'.format((width/height)/self.bbox.ratio,self.bbox.ratio/(width/height))
		
		return ((extent[0]-x_avg)*scale+x_avg,
				(extent[1]-y_avg)*scale+y_avg,
				(extent[2]-x_avg)*scale+x_avg,
				(extent[3]-y_avg)*scale+y_avg)
	
	def left_extent(self):
		full_extent = self.full_extent()
		#extent_overwidth = self.bbox.overwidth/self.bbox.width*(full_extent[2]-full_extent[0])/2
		extent_overwidth=0.
		return mapnik.Box2d(full_extent[0]-extent_overwidth,
				full_extent[1]-extent_overwidth*self.bbox.ratio,
				(full_extent[0]+full_extent[2])/2+extent_overwidth,
				full_extent[3]+extent_overwidth*self.bbox.ratio)
				
	def right_extent(self):
		full_extent = self.full_extent()
		extent_overwidth = self.bbox.overwidth/self.bbox.width*(full_extent[2]-full_extent[0])/2
		return mapnik.Box2d((full_extent[0]+full_extent[2])/2-extent_overwidth,
				full_extent[1]-extent_overwidth*self.bbox.ratio,
				full_extent[2]+extent_overwidth,
				full_extent[3]+extent_overwidth*self.bbox.ratio)
	
class Bbox:
	def __init__(self, startx, starty, width, ratio, overwidth=0., proj=mapnik.Projection('+init=epsg:3857')):
		'''
		Sets up a bounding box object. start[x|y] are the start coordinates in the projection proj
		
		Projections other than epsg:3857 may not work yet
		'''
		self.startx = float(startx)
		self.starty = float(starty)
		self.width = float(width)
		self.ratio = float(ratio)
		if type(overwidth) == types.FloatType:
			self.overwidth = overwidth
		elif type(overwidth) == types.StringTypes:
			if overwidth[-1] == '%':
				try:
					self.overwidth = float(overwidth[0,-1])
				except TypeError:
					raise ValueError('A string parameter for overwidth must be a percentage')
			else:
				raise ValueError('A string parameter for overwidth must be a percentage')
		else:
			raise TypeError('a float or string is required for overwidth')

	def bounds(self,page):
		'''
		Returns the bounds, given an (x,y) to offset by
		'''
		return (self.startx + page.x*self.width - self.overwidth, self.starty + (page.y*self.width - self.overwidth)*self.ratio,
				self.startx + (page.x+1)*self.width + self.overwidth, self. starty + ((page.y+1)*self.width + self.overwidth)*self.ratio)

class Sheet:
	'''
	The physical sheet
	'''
	def __init__(self, pagewidth, pageheight, padding):
		self.pagewidth = pagewidth
		self.pageheight = pageheight
		self.padding = padding

	@property
	def mapheight(self):
		return self.pageheight - 2 * self.padding
	
	@property
	def mapwidth(self):
		return self.pagewidth - self.padding
		
	@property
	def ratio(self):
		return float(self.mapheight)/self.mapwidth
	
	def page_inset(self,page):
		'''
		Returns the rectangle to place the map on 
		'''
		if page.right:
			return (0., float(self.padding), float(self.mapwidth), float(self.mapheight))
		else:
			return (float(self.padding), float(self.padding), float(self.mapwidth), float(self.mapheight))
	
	def draw_inset(self, ctx, page):
		ctx.rectangle(*(self.page_inset(page)))
	
class Pagelist:
	def __init__(self, rows, columns, start=1, skip=[],right=False):
		if type(rows) != types.IntType:
			raise TypeError('an int is required for rows')
		self.rows=rows
		if type(columns) != types.IntType:
			raise TypeError('an int is required for columns')
		self.columns=columns
		if type(start) != types.IntType:
			raise TypeError('an int is required for start')
		self.start=start
		if type(skip) != types.ListType:
			raise TypeError('a list is required for skip')
		for page in skip:
			if type(page) != types.IntType:
				raise TypeError('all members of skip must be ints')
		self.skip=skip
		self.right=bool(right)
		
	def __iter__(self):
		return Pagelist.pages(self)
	
	def number(self, x, y):
		'''
		Returns the number of a map given the x and y
		'''
		number = None
		if x>=0 and x<self.columns:
			if y>=0 and y<self.rows:
				number = y*self.rows + x + self.start
		if number not in self.skip:
			return number
		else:
			return None
		
	def pages(self):
		number = self.start
		pagecount = 2 - int(self.right)
		for y in range(0,self.rows):
			for x in range(0,self.columns):
				if number not in self.skip:
					yield Page(x,y,number,bool(pagecount % 2))
				number += 1
				pagecount += 1

class Page:
	def __init__(self, x, y, number,right):
		self.x = x
		self.y = y
		self.number = number
		self.right=bool(right)
		
def print_centered_text(ctx, text):
	'''
	Uses the toy text API to print text at the current location
	ctx.stroke() must be called for the text to appear
	'''
	ctx.rel_move_to(-float(ctx.text_extents(text)[2])/2, float(ctx.text_extents(text)[3])/2)
	ctx.show_text(text)

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
	bbox = Bbox(opts.startx, opts.starty, opts.width, sheet.ratio) 
	myarea = Area(Pagelist(opts.rows, opts.columns, opts.firstpage, skippedmaps, right=False), bbox, sheet, dpi=300.)
	mybook = Book(opts.outputfile,myarea,opts.mapfile,font='PT Sans')
	mybook.create_preface()
	mybook.create_maps()
	mybook._surface.finish()
	