from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from form_creator_app import models


def bind_args(field, **kwargs1):
    def wrapper(*args, **kwargs2):
        kwargs = {**kwargs1, **kwargs2}
        return field(*args, **kwargs)
    return wrapper


FIELD_BINDINGS = {
    'input': bind_args(forms.CharField, max_length=100),
    'textarea': bind_args(forms.CharField, widget=forms.Textarea),
    'select': forms.ChoiceField
}


class FormModelForm(forms.ModelForm):
    class Meta:
        model = models.Form
        fields = ('title',)


class FieldModelForm(forms.ModelForm):
    class Meta:
        model = models.FormField
        exclude = ('form',)


class FieldChoiceModelForm(forms.ModelForm):
    class Meta:
        model = models.FieldChoice
        exclude = ('field',)


class SelectOptionRequiredInlineFormset(BaseInlineFormSet):
    def clean(self):
        field_type = self.instance.type
        if field_type == 'select' and not self.has_changed():
            raise ValidationError('Select must have at least one option.')


class BaseFieldFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        try:
            instance = self.get_queryset()[index]  # TODO: Use .queryset?
        except IndexError:
            instance = None  # TODO: Check block required: instance doesn't have pk sometimes?

        form.choices = FieldChoiceInlineFormset(
            data=self.data or None,
            instance=instance,
            prefix=f'choices_formset_{index}'
        )

    def clean(self):
        for form in self.forms:
            if form['type'].value() == 'select':
                choices = form.choices
                at_least_one_choice = any(
                        choice['name'].value() for choice in choices
                    )
                if not at_least_one_choice:
                    raise ValidationError(
                        'Select field must have at least one option.'
                    )

    def is_valid(self):
        result = super().is_valid()
        choices_valid = []
        for form in self.forms:
            choices_fs = form.choices
            choices_valid.append(
                choices_fs.is_valid() and not choices_fs.non_form_errors()
            )
        return result and all(choices_valid)

    def save_new(self, form, commit=True):
        instance = super().save_new(form, commit=commit)

        choices = form.choices
        choices.instance = instance
        for data in choices.cleaned_data:
            data[choices.fk.name] = instance
        choices.save()


FieldInlineFormset = forms.inlineformset_factory(
    models.Form,
    models.FormField,
    form=FieldModelForm,
    extra=1,
    can_delete=False,
    formset=BaseFieldFormset
)

FieldChoiceInlineFormset = forms.inlineformset_factory(
    models.FormField,
    models.FieldChoice,
    form=FieldChoiceModelForm,
    extra=1,
    can_delete=False,
    formset=SelectOptionRequiredInlineFormset
)


class FormEntryForm(forms.ModelForm):
    class Meta:
        model = models.FormEntry
        exclude = ('uid',)


class FormCompiler:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.attrs = {
            'blueprint': blueprint,
            'save': self.get_form_save()
        }

    def compile_form(self):
        self.compile_fields(self.blueprint.fields.all())
        return type(
            self.blueprint.title,
            (forms.Form,),
            self.attrs
        )

    def compile_fields(self, fields):
        for field in fields:
            self.attrs[field.name] = self.compile_field(field)

    def compile_field(self, field):
        typ = field.type
        form_field = self.get_form_field(typ)

        if typ == 'select':
            choices = field.choices.values_list('name', flat=True)

            form_field = form_field(
                required=field.required,
                help_text=field.description,
                choices=zip(choices, choices)
            )
        else:
            form_field = form_field(
                required=field.required,
                help_text=field.description
            )
        return form_field

    def get_form_field(self, typ):
        return FIELD_BINDINGS[typ]

    def get_form_save(self):
        def save(self):
            data = {'form': self.blueprint, 'data': self.cleaned_data}
            entry = FormEntryForm(data)
            return entry.save()

        return save
