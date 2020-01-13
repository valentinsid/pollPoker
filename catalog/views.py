from django.shortcuts import render
import json
# Create your views here.
from django.db.models import F
from .models import Book, Author, BookInstance, Genre, Option,BigBlind
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
def index(request):
	"""View function for home page of site."""
	# Generate counts of some of the main objects
	num_books = Book.objects.all().count()
	num_instances = BookInstance.objects.all().count()
	# Available copies of books
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()
	num_authors = Author.objects.count()  # The 'all()' is implied by default.

	# Number of visits to this view, as counted in the session variable.
	num_visits = request.session.get('num_visits', 0)
	request.session['num_visits'] = num_visits+1

	# Render the HTML template index.html with the data in the context variable.
	return render(
		request,
		'index.html',
		context={'num_books': num_books, 'num_instances': num_instances,
				 'num_instances_available': num_instances_available, 'num_authors': num_authors,
				 'num_visits': num_visits},
	)


from django.views import generic


class BookListView(generic.ListView):
	"""Generic class-based view for a list of books."""
	model = Book
	paginate_by = 10


class BookDetailView(generic.DetailView):
	"""Generic class-based detail view for a book."""
	model = Book


class AuthorListView(generic.ListView):
	"""Generic class-based list view for a list of authors."""
	model = Author


	def get_context_data(self, **kwargs):
		print("ghghghghj")
		context = super(AuthorListView, self).get_context_data(**kwargs)
		
		try:
			context.update({
				"bb_value":BigBlind.objects.all().last().bb_sum
			})
		except AttributeError:	   
			context.update({
				"bb_value":"0"
				
			})
		return context	


class AuthorDetailView(generic.DetailView):
	"""Generic class-based detail view for an author."""
	model = Author

	obj = model.objects.first()
	field_name = 'id'
	try:
		field_object = model._meta.get_field(field_name)
		field_value = field_object.value_from_object(obj)
	except AttributeError:
		pass
	
	def get_context_data(self, **kwargs):
		context = super(AuthorDetailView, self).get_context_data(**kwargs)
		voted_users = context['author'].voted_id.split()
		print(voted_users)
		context.update({
			'choice_list': Option.objects.all(),
			'voted_users':voted_users,
			
		})

		return context
	def post(self, request, **kwargs):     
		a=kwargs['pk']
		
		print(request.POST.keys(),a,kwargs)
		vote(request, a)
		return render(request, 'index.html')    

from django.contrib.auth.mixins import LoginRequiredMixin


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	model = Author
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 10

	def get_queryset(self):
		return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


# Added as part of challenge!
from django.contrib.auth.mixins import PermissionRequiredMixin

# TO CHTO NADO
class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
	"""Generic class-based view listing all books on loan. Only visible to users with can_mark_returned permission."""
	
	permission_required = 'catalog.can_mark_returned'
	template_name = 'catalog/bookinstance_list_borrowed_all.html'
	paginate_by = 10
	model = Author
	

	def get_context_data(self, **kwargs):
		context = super(LoanedBooksAllListView, self).get_context_data(**kwargs)
		new_list=list(Option.objects.all())
		new_list2=list(Author.objects.all())
		new_list3 = list(User.objects.values_list('username', flat=True))
		
		k1=[]
		k11=[]
		#new_list_vote = list(Option.objects.all().votes)
		for i in new_list:

			k2=[i,i.votes]
			k1.append(k2)
		print(k1)	
		for i in k1:
			k11.append([str(i[0]),str(i[1])])  
		objectt=Author.objects.all()   
		print(len(new_list2))
		if objectt.count() == 2:
			objectt=objectt[1].voted_id.split()
			print(k11)
			context.update({
			'choice_list': json.dumps(k11),
			'voted_list':objectt,
			'author_list':new_list2,
			'user_list':new_list3,
			
		})   
		elif objectt.count() < 2:  
			context.update({
			'choice_list': json.dumps(k11),
			'user_list':new_list3,
			'author_list':new_list2,
			
		})
		
		
		return context    
	def get_queryset(self):
		return BookInstance.objects.filter(status__exact='o').order_by('due_back')
	def post(self, request, **kwargs):     
		a=kwargs['pk']
		print(a)
		print(request)
		print("UPDATE_VOTES POST")
		update_votes(request, a)
		return render(request, 'updated.html')      

#---------------------------------------------------------------------------------------------
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
# from .forms import RenewBookForm
from catalog.forms import RenewBookForm
from django.shortcuts import redirect

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
	"""View function for renewing a specific BookInstance by librarian."""
	book_instance = get_object_or_404(BookInstance, pk=pk)

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = RenewBookForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			book_instance.due_back = form.cleaned_data['renewal_date']
			book_instance.save()

			# redirect to a new URL:
			return HttpResponseRedirect(reverse('all-borrowed'))

	# If this is a GET (or any other method) create the default form
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

	context = {
		'form': form,
		'book_instance': book_instance,
	}

	return render(request, 'catalog/book_renew_librarian.html', context)


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text



class AuthorCreate(PermissionRequiredMixin, CreateView):
	model = Author

	fields = {'card'}
	
	
	def post(self, request, **kwargs):
		try:
			ee=Author.objects.create(card=request.POST.get('card'),bb=BigBlind.objects.all().last().bb_sum)
		except AttributeError:
			return HttpResponseRedirect(reverse('catalog:author_create')) 
		ee.save()
		return HttpResponseRedirect(reverse('catalog:author_create')) 
	
	permission_required = 'catalog.can_mark_returned'
	
	

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
	model = Author
	fields = {'card','bb'}
	success_url = reverse_lazy('catalog:authors')
	permission_required = 'catalog.can_mark_returned'




class StartGame(PermissionRequiredMixin, CreateView):
	model = Author
	
	fields = {'date_of_death'}

	permission_required = 'catalog.can_mark_returned'

	def post(self, request, **kwargs):
		bb_object = BigBlind.objects.create(bb_sum=request.POST.get('bigblind'))
		bb_object.save()
		
		print(request.POST.get('game_start'))
		if request.POST.get('game_start')=='on' and len(Author.objects.all())==0:
			ee=Author.objects.create(card='0',bb=0)
			ee.save()
		if request.POST.get('game_start')!='on' and len(Author.objects.all())!=0:
			Author.objects.all().delete()
			BigBlind.objects.all().delete()

		return HttpResponseRedirect(reverse('catalog:index')) 		
		
		
		
	def get_context_data(self, **kwargs):
		context = super(StartGame, self).get_context_data(**kwargs)
		if BigBlind.objects.all().last().bb_sum:
			context.update({
				"bb_value":BigBlind.objects.all().last().bb_sum
			})
		else:	   
			context.update({
				"bb_value":0
				
			})
		return context	

class AuthorDelete(PermissionRequiredMixin, DeleteView):
	
	
	model = Author
	
	success_url = reverse_lazy('catalog:author_create')
	permission_required = 'catalog.can_mark_returned'
	def post(self, request, **kwargs):
		print(self,kwargs)
		deleted_card = Author.objects.get(id=kwargs['pk'])
		if deleted_card=='0':
			deleted_card.delete()
			return HttpResponseRedirect(reverse_lazy('catalog:index'))
		else:
			deleted_card.delete()
			return HttpResponseRedirect(reverse_lazy('catalog:all-borrowed'))



# Classes created for the forms challenge
class BookCreate(PermissionRequiredMixin, CreateView):
	model = Book
	fields = '__all__'
	permission_required = 'catalog.can_mark_returned'


class BookUpdate(PermissionRequiredMixin, UpdateView):
	model = Book
	fields = '__all__'
	permission_required = 'catalog.can_mark_returned'


class BookDelete(PermissionRequiredMixin, DeleteView):
	model = Book
	success_url = reverse_lazy('books')
	permission_required = 'catalog.can_mark_returned'



from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

def votefail(request):
	return redirect('catalog/votefailed.html')   


def vote(request, author_id):
	
	try:
		author = Author.objects.all().get(pk=author_id)
	except ObjectDoesNotExist:
		
		return HttpResponseRedirect(reverse('catalog:votefailed'))    
	a= LogEntry.objects.log_action(
	user_id         = request.user.pk, 
	content_type_id = ContentType.objects.get_for_model(Option).pk,
	object_id       = Option.pk,
	object_repr     = force_text(Option), 
	action_flag     = CHANGE
)
	
	
	try:
		print(request.POST)
		selected_choice = author.option_set.get(pk=request.POST['btn'])
		
		
	except (KeyError, Option.DoesNotExist):
		# Redisplay the question voting form.
		pass
	else:
		if author.voted_id == "zero":
			author.voted_id = str(User.objects.get(pk=a.user_id))+" "
		else:
			author.voted_id += str(User.objects.get(pk=a.user_id))+" "

		author.save(update_fields=["voted_id"]) 
		print(author.voted_id)
		selected_choice.votes = F("votes") + 1
		selected_choice.save()
		# Always return an HttpResponseRedirect after successfully dealing
		# with POST data. This prevents data from being posted twice if a
		# user hits the Back button.
		print("redirect2")
		return HttpResponseRedirect(reverse('catalog:author_create'))

def update_votes(request,*args, **kwargs):
	print("UPDATE_VOTES FUNK")
	print(request,kwargs)
	author = get_object_or_404(Author, pk=kwargs['pk'])
	author.voted_id="zero"
	author.save(update_fields=["voted_id"])
	print(author)
	print("UPDATE_VOTES FUNK 2")
	Option.objects.all().update(votes=0)
	return HttpResponseRedirect(reverse('catalog:all-borrowed'))  


def redir(request,*args, **kwargs):
	
	return HttpResponseRedirect(reverse('catalog:index'))   	      




from django.shortcuts import render

from django.template import Context, loader


##
# Handle 404 Errors
# @param request WSGIRequest list with all HTTP Request
def error404(request,exception=None):

	# 1. Load models for this view
	#from idgsupply.models import My404Method

	# 2. Generate Content for this view
	
	return redirect('catalog:index')
