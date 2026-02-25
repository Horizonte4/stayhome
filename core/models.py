from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class SlugModel(models.Model):
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.slug:
            source = getattr(self, 'titulo', '') or getattr(self, 'name', '')
            self.slug = slugify(source)[:200]
        super().save(*args, **kwargs)

# Modelo final combinando mixins:
class Propiedad(TimeStampedModel, SoftDeleteModel, SlugModel):
    titulo = models.CharField(max_length=200)
    # La propiedad ahora tiene: created_at, updated_at, is_deleted, deleted_at, slug