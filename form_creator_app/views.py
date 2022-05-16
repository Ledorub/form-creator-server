import json
from functools import wraps
from django.shortcuts import HttpResponse, reverse, render, redirect
from django import views
from django.http import JsonResponse
from django.db import transaction
from django.template.loader import render_to_string
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from form_creator_app import forms, models
from form_creator_app.json_rpc import Dispatcher, RPCRequest


class HomeView(views.View):
    template_name = 'form_creator_app/home.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        form_uid = request.POST.get('form_uid', None)
        if not form_uid:
            return redirect(self.request.get_full_path())
        kwargs = {'form_uid': form_uid}
        return redirect(reverse('form-creator-app:data-list', kwargs=kwargs))


class FormCreatorView(CreateView):
    """
    Renders form to construct another form.
    """
    model = models.Form
    form_class = forms.FormModelForm
    template_name = 'form_creator_app/form_creator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields_formset'] = forms.FieldInlineFormset(
            self.request.POST or None,
            instance=self.object or None,
            prefix='fields_formset'
        )
        return context

    def form_valid(self, form):
        result = super().form_valid(form)

        context = self.get_context_data()
        fields_formset = context['fields_formset']

        with transaction.atomic():
            if not fields_formset.is_valid():
                return self.form_invalid(form)
            fields_formset.save()
            form.save()

        return result

    def get_success_url(self):
        kwargs = {'form_uid': self.object.uid}
        return reverse('form-creator-app:form-created', kwargs=kwargs)


def form_created_view(request, form_uid):
    """
    Renders a form_uid of newly created form.
    Used as a success url for form creator.
    """
    template_name = 'form_creator_app/form_created.html'
    return render(request, template_name, {'form_uid': form_uid})


class FormDataListView(ListView):
    """
    Renders all data related to a given form (form_uid).
    """
    model = models.FormEntry
    template_name = 'form_creator_app/data.html'

    def get_queryset(self):
        return self.model.objects.filter(form__uid=self.kwargs['form_uid'])


def json_rpc_decorator(view):
    """
    Extracts JSONRPC request data to RPCRequest object.
    Wraps view response into RPCResponse object.
    """
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        request_data = json.loads(request.body)
        rpc_request = RPCRequest(**request_data)

        response = view(request, *args, rpc_request=rpc_request, **kwargs)

        response_data = json.loads(response.content)
        response_data = rpc_request.prepare_response(result=response_data).as_dict()
        return JsonResponse(response_data)
    return wrapper


class FormView(views.View):
    """
    Handles RPC API calls.
    """
    form_compiler = forms.FormCompiler

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(json_rpc_decorator)
    def post(self, request, *args, **kwargs):
        rpc_request = kwargs.get('rpc_request')
        result = dispatcher.dispatch(rpc_request)['result']
        if 'error' in result:
            return JsonResponse(result)

        template_name = result.get('template_name', None)
        if template_name:
            rendered = render_to_string(template_name, result['context'])
            result = {'ok': result['ok'], 'form': rendered}
        else:
            data = result.get('context', {})
            result = {'ok': result['ok'], **data}
        return JsonResponse(result)


class JSONRPCMethods:
    """
    Just a collection of supported JSONRPC methods.
    """
    @staticmethod
    def _prepare_result(ok, context=None, template=None):
        result = {
            'ok': ok,
        }
        if context:
            result['context'] = context
        if template:
            result['template_name'] = template
        return result

    @staticmethod
    def get_form(form_uid):
        """
        Builds a form for a given UID.
        :param form_uid:
        :type form_uid:
        :return:
        :rtype:
        """
        definition = models.Form.objects.get(uid=form_uid)
        form = forms.FormCompiler(definition).compile_form()
        context = {'title': definition.title, 'form': form()}
        template_name = 'form_creator_app/form.html'
        result = JSONRPCMethods._prepare_result(True, context, template_name)
        return result

    @staticmethod
    def post_form(**kwargs):
        """
        Handles form filling process.
        """
        template_name = 'form_creator_app/form.html'
        form_uid = kwargs.get('form_uid')
        form_data = kwargs.get('form_data')
        definition = models.Form.objects.get(uid=form_uid)

        form = forms.FormCompiler(definition).compile_form()
        form = form(form_data)

        if form.is_valid():
            instance = form.save()
            data = {'data_uid': instance.uid}
            result = JSONRPCMethods._prepare_result(True, data)
        else:
            context = {'title': definition.title, 'form': form}
            result = JSONRPCMethods._prepare_result(False, context, template_name)
        return result

    @staticmethod
    def get_form_data(**kwargs):
        """
        Returns all data entries obtained by form UID.
        """
        form_uid = kwargs.get('form_uid')
        form_entries = models.Form.objects.get(uid=form_uid).entries.all()
        data = [{'uid': entry[0], 'data': entry[1]}
                for entry in form_entries.values_list('uid', 'data')]
        data = {'form_data': data}
        return JSONRPCMethods._prepare_result(True, data)


def register_jsonrpc_methods():
    """
    Registers RPC methods in dispatcher by their function names.
    """
    methods = [
        JSONRPCMethods.get_form,
        JSONRPCMethods.post_form,
        JSONRPCMethods.get_form_data
    ]
    for method in methods:
        dispatcher.register(method, method.__name__)


dispatcher = Dispatcher()
register_jsonrpc_methods()
