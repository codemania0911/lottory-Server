from django import forms
from .models import userinfo

class UserInfoCreateForm(forms.ModelForm):
    class Meta:
        model=userinfo
        fields=('id','name','password')
