import uuid

from django.db import models
from form_creator_app.utils import aware_utc_now


class FormField(models.Model):
    """
    Represents form field of on of the following type:
    input[text], textarea, select
    """
    TYPE_CHOICES = (
        ('input', 'Input'),
        ('textarea', 'Textarea'),
        ('select', 'Select')
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, null=True)
    required = models.BooleanField(default=False, blank=True)
    form = models.ForeignKey(
        'Form',
        related_name='fields',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.type}_{self.name}'


class FieldChoice(models.Model):
    """
    Represents options for select field.
    """
    name = models.CharField(max_length=100)
    field = models.ForeignKey(
        'FormField',
        related_name='choices',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.field}_choice_{self.name}'


class Form(models.Model):
    """
    Stores data required to build a form.
    """
    uid = models.UUIDField(default=uuid.uuid4)
    title = models.CharField(max_length=100)
    date_created = models.DateTimeField(default=aware_utc_now)

    def __str__(self):
        return f'{self.title}'


class FormEntry(models.Model):
    """
    Data related to dynamically built form.
    """
    uid = models.UUIDField(default=uuid.uuid4)
    form = models.ForeignKey(
        'Form',
        related_name='entries',
        on_delete=models.CASCADE
    )
    data = models.JSONField()
