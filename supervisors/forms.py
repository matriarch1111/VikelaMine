from django import forms
from core.models import HazardResponse


class HazardResponseForm(forms.ModelForm):
    class Meta:
        model = HazardResponse
        fields = ["comment", "evidence_photo"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }
        