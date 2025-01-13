from django.shortcuts import redirect


class LegalRequirementMixin:
    def dispatch(self, request, *args, **kwargs):

        if not request.user.legaluser.privacy:
            return redirect("privacy")

        if not request.user.legaluser.terms:
            return redirect("terms")

        if not request.user.legaluser.disclaimer:
            return redirect("disclaimer")

        return super().dispatch(request, *args, **kwargs)


class ProtectionRequirementMixin:
    def dispatch(self, request, *args, **kwargs):

        if request.user.legaluser.protection is None:
            return redirect("pedoguard")

        return super().dispatch(request, *args, **kwargs)
