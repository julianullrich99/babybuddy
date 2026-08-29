# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .models import Settings


class BabyBuddyUserForm(forms.ModelForm):
    is_read_only = forms.BooleanField(
        required=False,
        label=_("Read only"),
        help_text=_("Restricts user to viewing data only."),
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_read_only",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs["instance"]
        if user:
            kwargs["initial"].update(
                {
                    "is_read_only": user.groups.filter(
                        name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
                    ).exists()
                }
            )
        super(BabyBuddyUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super(BabyBuddyUserForm, self).save(commit=False)
        is_read_only = self.cleaned_data["is_read_only"]
        if is_read_only:
            user.is_superuser = False
        else:
            user.is_superuser = True
        if commit:
            user.save()
        readonly_group = Group.objects.get(
            name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
        )
        if is_read_only:
            user.groups.add(readonly_group.id)
        else:
            user.groups.remove(readonly_group.id)
        return user


class UserAddForm(BabyBuddyUserForm, UserCreationForm):
    pass


class UserUpdateForm(BabyBuddyUserForm):
    pass


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]


class UserPasswordForm(PasswordChangeForm):
    class Meta:
        fields = ["old_password", "new_password1", "new_password2"]


class UserSettingsForm(forms.ModelForm):
    dashboard_cards = forms.MultipleChoiceField(
        label=_("Dashboard cards"),
        help_text=_(
            "Cards to show on child dashboards, in the order they appear here."
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    # Maintained by the move up/down controls in the settings template as a
    # comma-separated list of card identifiers.
    dashboard_card_order = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "dashboard-card-order__value"}),
    )

    class Meta:
        model = Settings
        fields = [
            "dashboard_refresh_rate",
            "dashboard_hide_empty",
            "dashboard_hide_age",
            "language",
            "timezone",
            "pagination_count",
        ]

    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        # Imported here to avoid a circular import at module load time.
        from dashboard.cards import get_ordered_card_choices, order_card_ids

        # Choices are presented in the user's own card order so that the
        # checkbox list doubles as the ordering control.
        card_ids = order_card_ids(self.instance.dashboard_card_order)
        self.fields["dashboard_cards"].choices = get_ordered_card_choices(card_ids)
        hidden = set(self.instance.dashboard_hidden_cards or [])
        self.initial["dashboard_cards"] = [
            card_id for card_id in card_ids if card_id not in hidden
        ]
        self.initial["dashboard_card_order"] = ",".join(card_ids)

    def clean_dashboard_card_order(self):
        """
        Normalize the submitted order against the cards that actually exist.
        Unknown and duplicated identifiers are dropped and anything missing is
        appended, so a stale or hand-edited value can never drop a card.
        """
        submitted = [
            card_id.strip()
            for card_id in (self.cleaned_data.get("dashboard_card_order") or "").split(
                ","
            )
            if card_id.strip()
        ]
        known = [card_id for card_id, _label in self.fields["dashboard_cards"].choices]

        ordered = []
        seen = set()
        for card_id in submitted:
            if card_id in known and card_id not in seen:
                ordered.append(card_id)
                seen.add(card_id)
        ordered += [card_id for card_id in known if card_id not in seen]
        return ordered

    def save(self, commit=True):
        instance = super(UserSettingsForm, self).save(commit=False)
        # Visible cards are stored as their complement so that newly added
        # cards (and activity types) are shown by default.
        visible = set(self.cleaned_data.get("dashboard_cards") or [])
        instance.dashboard_hidden_cards = [
            card_id
            for card_id, _label in self.fields["dashboard_cards"].choices
            if card_id not in visible
        ]
        instance.dashboard_card_order = self.cleaned_data.get("dashboard_card_order")
        if commit:
            instance.save()
        return instance
