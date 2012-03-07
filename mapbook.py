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
		self._ctx.set_line_width(.4)
		self._ctx.set_source_rgb(0, 0, 0)
		self.area.sheet.draw_inset(self._ctx,Page(None, None, None, False))
		self._ctx.stroke()

		self._ctx.set_line_width(1)
		self._ctx.set_source_rgb(0.5, 0.5, 0.5)		
		for page in self.area.pagelist:
			self.area.sheet.draw_bbox(self._ctx,self.area.bbox.bounds(page),self.area.left_extent())
		self._ctx.stroke()
		
		self._ctx.show_page()
		
		self._render_map(Page(None, None, None, True), self.area.right_extent())
		
		self._ctx.set_line_width(.4)
		self._ctx.set_source_rgb(0, 0, 0)
		self.area.sheet.draw_inset(self._ctx,Page(None, None, None, True))
		self._ctx.stroke()

		self._ctx.set_line_width(1)
		self._ctx.set_source_rgb(0.5, 0.5, 0.5)		
		for page in self.area.pagelist:
			self.area.sheet.draw_bbox(self._ctx,self.area.bbox.bounds(page),self.area.right_extent())
		self._ctx.stroke()
		
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
		self._ctx.set_font_size(self.area.sheet.padding*.4)
		self._render_arrow_text(page)
		self._ctx.stroke()
		
		self._ctx.set_source_rgb(0., 0., 0.)
		self._render_number_path(page)
		self._ctx.fill()
		
		self._ctx.set_source_rgb(1., 1., 1.) 
		self._ctx.select_font_face(self.font)
		self._ctx.set_font_size(self.area.sheet.padding*.8)
		self._render_number_text(page)
		self._ctx.stroke()
		
		self._ctx.show_page()

	def _render_map(self, page, bbox):
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
		
		ratio = 0.5*self.bbox.ratio
		if height/width < ratio:
			return (x_avg-0.5*width, y_avg-0.5*width*ratio, x_avg+0.5*width, y_avg+0.5*width*ratio)
		else:
			return (x_avg-0.5*height/ratio, y_avg-0.5*height, x_avg+0.5*height/ratio, y_avg+0.5*height)

	def left_extent(self):
		full_extent = self.full_extent()
		extent_overwidth = self.bbox.overwidth/self.bbox.width*(full_extent[2]-full_extent[0])/2
		
		map_region = 	(full_extent[0]-extent_overwidth,
						full_extent[1]-extent_overwidth*self.bbox.ratio,
						(full_extent[0]+full_extent[2])/2+extent_overwidth,
						full_extent[3]+extent_overwidth*self.bbox.ratio)
		y_avg = (map_region[3]+map_region[1])/2
		return mapnik.Box2d(
								(map_region[0]-map_region[2])*float(self.pagesize_pixels[0])/self.map_size[0]+map_region[2],
								(map_region[1]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg,
								map_region[2],
								(map_region[3]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg)
	def right_extent(self):
		full_extent = self.full_extent()
		extent_overwidth = self.bbox.overwidth/self.bbox.width*(full_extent[2]-full_extent[0])/2
		map_region =	((full_extent[0]+full_extent[2])/2-extent_overwidth,
						full_extent[1]-extent_overwidth*self.bbox.ratio,
						full_extent[2]+extent_overwidth,
						full_extent[3]+extent_overwidth*self.bbox.ratio)
		y_avg = (map_region[3]+map_region[1])/2		
		return mapnik.Box2d(
									map_region[0],
									(map_region[1]-y_avg)*float(self.pagesize_pixels[1])/self.map_size[1]+y_avg,
									(map_region[2]-map_region[0])*float(self.pagesize_pixels[0])/self.map_size[0]+map_region[0],
									(map_region[3]-y_avg)*self.pagesize_pixels[1]/self.map_size[1]+y_avg)	
	
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
	
	def draw_bbox(self, ctx, bbox, extents):
		'''
		Draws the rectangle bbox on a page with a map covering extents
		'''
		bounds_on_page =	(self._x_location_from_bounds(bbox[0], extents), 
							self._y_location_from_bounds(bbox[1], extents), 
							self._x_location_from_bounds(bbox[2], extents), 
							self._y_location_from_bounds(bbox[3], extents))
		ctx.rectangle(bounds_on_page[0], bounds_on_page[1], bounds_on_page[2]-bounds_on_page[0], bounds_on_page[3]-bounds_on_page[1])
		
	def _x_location_from_bounds(self, x, bounds):
		return float(x-bounds[0])/(bounds[2]-bounds[0])*self.pagewidth
		
	def _y_location_from_bounds(self, y, bounds):
		return float(y-bounds[3])/(bounds[1]-bounds[3])*self.pageheight
	
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
				number = y*self.columns + x + self.start
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
