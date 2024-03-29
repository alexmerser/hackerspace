from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from notifications.signals import notify

from comments.forms import CommentForm
from comments.models import Comment

from .models import Announcement
from .forms import AnnouncementForm

#function based views..

@login_required
def comment(request, id):
    announcement = get_object_or_404(Announcement, pk=id)
    origin_path = announcement.get_absolute_url()

    if request.method == "POST":

        form = CommentForm(request.POST)

        if form.is_valid():
            comment_text = form.cleaned_data.get('comment_text')
            if not comment_text:
                comment_text = ""
            comment_new = Comment.objects.create_comment(
                user = request.user,
                path = origin_path,
                text = comment_text,
                target = announcement,
            )

            if 'comment_button' in request.POST:
                note_verb="commented on"
                # icon = "<i class='fa fa-lg fa-comment-o text-info'></i>"
                icon="<span class='fa-stack'>" + \
                    "<i class='fa fa-newspaper-o fa-stack-1x'></i>" + \
                    "<i class='fa fa-comment-o fa-stack-2x text-info'></i>" + \
                    "</span>"
                if request.user.is_staff:
                    #get other commenters on this announcement
                    affected_users = None
                else:  # student comment
                    affected_users = User.objects.filter(is_staff=True)
            else:
                raise Http404("unrecognized submit button")

            notify.send(
                request.user,
                action=comment_new,
                target= announcement,
                recipient=request.user,
                affected_users=affected_users,
                verb=note_verb,
                icon=icon,
            )
            messages.success(request, ("Announcement " + note_verb))
            return redirect(origin_path)
        else:
            messages.error(request, "There was an error with your comment.")
            return redirect(origin_path)
    else:
        raise Http404


@login_required
def list(request, id=None):
    if request.user.is_staff:
        object_list = Announcement.objects.get_active()
    else:
        object_list = Announcement.objects.get_for_students()

    paginator = Paginator(object_list, 15)
    page = request.GET.get('page')
    active_id = 0
    # we want the page of a specific object
    if id is not None:
        active_obj = get_object_or_404(Announcement, pk=id)
        for pg in paginator.page_range:
            object_list = paginator.page(pg)
            if active_obj in object_list:
                page = pg
                active_id = int(id)
                break

    try:
        object_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        object_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        object_list = paginator.page(paginator.num_pages)

    comment_form = CommentForm(request.POST or None, label="")

    context = {
        'comment_form': comment_form,
        'object_list': object_list,
        'active_id': active_id,
    }
    return render(request, 'announcements/list.html', context)

@staff_member_required
def copy(request, id):
    new_ann = get_object_or_404(Announcement, pk=id)
    new_ann.pk = None # autogen a new primary key (quest_id by default)
    new_ann.title = "Copy of " + new_ann.title

    form = AnnouncementForm(request.POST or None, instance = new_ann)
    if form.is_valid():
        new_announcement = form.save(commit=False)
        new_announcement.author = request.user
        new_announcement.datetime_created = timezone.now
        new_announcement.save()
        form.save()

        if not new_announcement.draft:
            send_notifications(request, new_announcement)
        return redirect(new_announcement)

    context = {
        "title": "",
        "heading": "Copy an Announcement",
        "form": form,
        "submit_btn_value": "Create",
    }
    return render(request, "announcements/form.html", context)

@staff_member_required
def publish(request, id):
    announcement = get_object_or_404(Announcement, pk=id)
    announcement.draft = False
    announcement.save()
    send_notifications(request, announcement)
    return redirect(announcement)

def send_notifications(request, announcement):
        affected_users = User.objects.all().filter(is_active=True)
        notify.send(
            request.user,
            # action=new_announcement,
            target=announcement,
            recipient=request.user,
            affected_users=affected_users,
            icon="<i class='fa fa-lg fa-fw fa-newspaper-o text-info'></i>",
            verb='posted')

class Create(CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/form.html'

    def form_valid(self, form):
        new_announcement = form.save(commit=False)
        new_announcement.author = self.request.user
        new_announcement.save()

        if not new_announcement.draft:
            send_notifications(self.request, new_announcement)

        # new_announcement.send_by_mail()

        return super(Create, self).form_valid(form)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(Create, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['heading'] = "Create New Announcement"
        context['action_value']= ""
        context['submit_btn_value']= "Publish"
        return context

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(Create, self).dispatch(*args, **kwargs)

class Update(UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/form.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(Update, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['heading'] = "Edit Announcement"
        context['action_value']= ""
        context['submit_btn_value']= "Update"
        return context

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(Update, self).dispatch(*args, **kwargs)

class Delete(DeleteView):
    model = Announcement
    template_name = 'announcements/delete.html'
    success_url = reverse_lazy('announcements:list')

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(Delete, self).dispatch(*args, **kwargs)
