from django.urls import path, reverse_lazy
from form_creator_app import views
from form_creator_app.apps import APP_NAME

app_name = APP_NAME
urlpatterns = [
    path(
        'create/',
        views.FormCreatorView.as_view(
            success_url=reverse_lazy('form_creator_app:created')),
        name='form-creator'
    ),
    path(
        'created/<uuid:form_uid>/',
        views.form_created_view,
        name='form-created'
    ),
    path(
        'data/<uuid:form_uid>/',
        views.FormDataListView.as_view(),
        name='data-list'
    ),
    path(
        'api/form/',
        views.FormView.as_view(),
        name='api-form'
    )
]
