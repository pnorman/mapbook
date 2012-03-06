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
		pass
		
	def create_index(self):
		pass
	
	def create_maps(self):
		for page in self.area.pagelist:
			print "Rendering page {}".format(page.number)
			self._render_page(page)
			
	def _render_page(self, page):
		self._render_map(page)
		
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

	def _render_map(self, page):
		self._m.zoom_to_box(self.area.full_bounds(page))
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
	
	def extent(self):
		'''
		Returns the bbox of the overview page, without a padding allowance
		'''
		min_x = min(page.x for page in self.pagelist)
		min_y = min(page.y for page in self.pagelist)
		min_x = max(page.x for page in self.pagelist)
		min_y = max(page.y for page in self.pagelist)
		
		return (self.bbox.bounds(Page(min_x,min_y,0,False))[0]-(max_x-min_x+1)*bbox.overwidth,
				self.bbox.bounds(Page(min_x,min_y,0,False))[1]-(max_y-min_y+1)*bbox.overwidth*bbox.ratio,
				self.bbox.bounds(Page(min_x,min_y,0,False))[2]+(max_x-min_x+1)*bbox.overwidth,
				self.bbox.bounds(Page(min_x,min_y,0,False))[3]+(max_y-min_x+1)*bbox.overwidth*bbox.ratio)

class Bbox:
	def __init__(self, startx, starty, width, ratio, overwidth=0., proj=mapnik.Projection('+init=epsg:3857')):
		'''
		Sets up a bounding box object. start[x|y] are the start coordinates in the projection proj
		
		Projections other than epsg:3857 may not work yet
		'''
		self.startx = startx
		self.starty = starty
		self.width = width
		self.ratio=ratio
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
	def __init__(self, rows, columns, start=1, skip=[],right=True):
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
		if type(x) != types.IntType:
			raise TypeError('an int is required for x')
		self.x = x
		if type(y) != types.IntType:
			raise TypeError('an int is required for y')
		self.y = y
		if type(number) != types.IntType:
			raise TypeError('an int is required for y')
		self.number = number
		self.right=right
		
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
	myarea = Area(Pagelist(opts.rows, opts.columns, opts.firstpage, skippedmaps, right=True), bbox, sheet, dpi=300.)
	mybook = Book(opts.outputfile,myarea,opts.mapfile,font='PT Sans')
	mybook.create_maps()
	mybook._surface.finish()

	

if False:	
	# Initial mapnik setup
	merc = mapnik.Projection('+init=epsg:3857')
	m = mapnik.Map(int(opts.pagewidth*opts.dpi/72.0),int(opts.pageheight*opts.dpi/72.0))
	
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
		thisrow=[]
		for x in range(opts.columns):
			thisrow.append(None if opts.firstmap+y*opts.columns+x in skippedmaps else opts.firstmap+y*opts.columns+x)
		pagegrid.append(thisrow)
	

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
		ctx.show_page()
		pagecount = pagecount + 1

		
	# Print the legend page
	
	bounds = (\
	opts.startx - opts.columns*opts.overwidth,\
	opts.starty - opts.rows*opts.overwidth,\
	opts.startx + opts.columns*opts.width + opts.columns*opts.overwidth,\
	opts.starty + opts.columns*opts.width*mapheight/mapwidth + opts.columns*opts.overwidth\
	)
	
	bbox = (\
	bounds[0] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (bounds[2] - bounds[0]),\
	bounds[1] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (bounds[3] - bounds[1]),\
	bounds[2] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (bounds[2] - bounds[0]),\
	bounds[1] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (bounds[3] - bounds[1])\
	)
	m.aspect_fix_mode=mapnik.aspect_fix_mode.GROW_BBOX
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
	

	# Restore the clip region
	ctx.restore()
	
	ctx.set_line_width(.25)
	ctx.set_source_rgb(0, 0, 0)
	if pagecount % 2 != 1:
		ctx.rectangle(opts.pagepadding,opts.pagepadding,mapwidth,mapheight)
	else:
		ctx.rectangle(0,opts.pagepadding,mapwidth,mapheight)
	ctx.stroke()
	ctx.show_page()
	pagecount = pagecount + 1
	
	for page in pages:
		
		if not page.mapnumber:
			continue
			
		print 'Rendering map {} on page {}'.format(page.mapnumber, pagecount)
		
		#pages[0].bounds[0] - overwidth - 0.5 * (mwidth-width)
		# = . . .                             *(opts.pagewidth/mapwidth-1)*width
		# minx, miny, maxx, maxy

		bbox = (\
		page.bounds[0] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (page.bounds[2] - pages[0].bounds[0]),\
		page.bounds[1] - 2*opts.overwidth - 0.5 * (opts.pagewidth/mapwidth - 1) * (page.bounds[3] - page.bounds[1]),\
		page.bounds[2] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (page.bounds[2] - page.bounds[0]),\
		page.bounds[1] + 2*opts.overwidth + 0.5 * (opts.pagewidth/mapwidth - 1) * (page.bounds[3] - page.bounds[1])\
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

	