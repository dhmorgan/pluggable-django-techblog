from django import forms

class WriterForm(forms.Form):

    title = forms.CharField(label="Post Title", required=True)
    slug = forms.CharField(label="Post Slug", required=True)


    content = forms.CharField(label="Post Content", required=False)
