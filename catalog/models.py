from django.db import models

# Create your models here.

from django.urls import reverse  # To generate URLS by reversing URL patterns


class Genre(models.Model):
	"""Model representing a book genre (e.g. Science Fiction, Non Fiction)."""
	name = models.CharField(
		max_length=200,
		help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)"
		)

	def __str__(self):
		"""String for representing the Model object (in Admin site etc.)"""
		return self.name


class Language(models.Model):
	"""Model representing a Language (e.g. English, French, Japanese, etc.)"""
	name = models.CharField(max_length=200,
							help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

	def __str__(self):
		"""String for representing the Model object (in Admin site etc.)"""
		return self.name


class Book(models.Model):
	"""Model representing a book (but not a specific copy of a book)."""
	title = models.CharField(max_length=200)
	author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
	# Foreign Key used because book can only have one author, but authors can have multiple books
	# Author as a string rather than object because it hasn't been declared yet in file.
	summary = models.TextField(max_length=1000, help_text="Enter a brief description of the book")
	isbn = models.CharField('ISBN', max_length=13,
							help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn'
									  '">ISBN number</a>')
	genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
	# ManyToManyField used because a genre can contain many books and a Book can cover many genres.
	# Genre class has already been defined so we can specify the object above.
	language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)

	def display_genre(self):
		"""Creates a string for the Genre. This is required to display genre in Admin."""
		return ', '.join([genre.name for genre in self.genre.all()[:3]])

	display_genre.short_description = 'Genre'

	def get_absolute_url(self):
		"""Returns the url to access a particular book instance."""
		return reverse('book-detail', args=[str(self.id)])

	def __str__(self):
		"""String for representing the Model object."""
		return self.title


import uuid  # Required for unique book instances
from datetime import date

from django.contrib.auth.models import User  # Required to assign User as a borrower


class BookInstance(models.Model):
	"""Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4,
						  help_text="Unique ID for this particular book across whole library")
	book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True)
	imprint = models.CharField(max_length=200)
	due_back = models.DateField(null=True, blank=True)
	borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

	@property
	def is_overdue(self):
		if self.due_back and date.today() > self.due_back:
			return True
		return False

	LOAN_STATUS = (
		('d', 'Maintenance'),
		('o', 'On loan'),
		('a', 'Available'),
		('r', 'Reserved'),
	)

	status = models.CharField(
		max_length=1,
		choices=LOAN_STATUS,
		blank=True,
		default='d',
		help_text='Book availability')

	class Meta:
		ordering = ['due_back']
		permissions = (("can_mark_returned", "Set book as returned"),)

	def __str__(self):
		"""String for representing the Model object."""
		return '{0} ({1})'.format(self.id, self.book.title)


class Author(models.Model):
	"""Model representing an author."""

	first_card = models.CharField(max_length=100)
	second_card = models.CharField(max_length=100)
	date_of_birth = models.DateField(null=True, blank=True)
	date_of_death = models.DateField('died', null=True, blank=True)
	bb = models.IntegerField(default=0)
	voted_id = models.CharField(max_length=1000,default="zero")

	class Meta:
		ordering = ['first_card', 'second_card']

	def get_absolute_url(self):
		"""Returns the url to access a particular author instance."""
		return reverse('catalog:author-detail', args=[str(self.id)])

	def __str__(self):
		"""String for representing the Model object."""
		return '{0}, {1}'.format(self.first_card, self.second_card)



	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		print('SAVED')

		Option.objects.all().update(author_id=self.id)
		if Author.objects.get(pk=self.id):
			print("HAI")
		else:
			print("dsadsa")
			Option.objects.all().update(votes=0)



	def delete(self, *args, **kwargs):
		Option.objects.filter(author_id=self.id).update(author_id=None, votes=0)
		super().delete(*args, **kwargs)
		   



class Option(models.Model):
	
	def default_votes():
		d=Author.objects.all().first()
		
		for a in d.option_set.all():
			a.votes=0


		return d
	author = models.ForeignKey(Author, on_delete=models.SET_NULL, default=default_votes,null=True)
	
	choice_text = models.CharField(max_length=200)
	votes = models.IntegerField(default=0)
	
	def __str__(self):
		return self.choice_text





