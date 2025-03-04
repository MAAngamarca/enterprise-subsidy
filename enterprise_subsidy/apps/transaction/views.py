"""
Views for the openedx_ledger app.
"""
import logging

import requests
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from openedx_ledger.models import Transaction

from enterprise_subsidy.apps.api_client.enterprise import EnterpriseApiClient

logger = logging.getLogger(__name__)


# endpoints routed behind the `admin/` namespace are by default given staff or super user permissions level access
class UnenrollLearnersView(View):
    """
    Admin view for the canceling platform enrollments form.
    """
    template = "admin/unenroll.html"

    def get(self, request, transaction_id):
        """
        Handle GET request - render "Cancel transaction without refund" form.

        Arguments:
            request (django.http.request.HttpRequest): Request instance
            transaction_uuid (str): Enterprise Customer UUID

        Returns:
            django.http.response.HttpResponse: HttpResponse
        """
        transaction = Transaction.objects.filter(uuid=transaction_id).first()

        if not transaction:
            logger.info(f"UnenrollLearnersView: transaction {transaction_id} not found, skipping")
            return HttpResponseBadRequest("Transaction not found")
        if not transaction.fulfillment_identifier:
            logger.info(f"UnenrollLearnersView: transaction {transaction_id} has no fulfillment uuid, skipping")
            return HttpResponseBadRequest("Transaction has no associated platform fulfillment identifier")

        return render(
            request,
            self.template,
            {'transaction': Transaction.objects.get(uuid=transaction_id)}
        )

    def post(self, request, transaction_id):
        """
        Handle POST request - handle form submissions.

        Arguments:
            request (django.http.request.HttpRequest): Request instance
        """
        logger.info(f"Sending admin invoked transaction unenroll signal for transaction: {transaction_id}")
        transaction = Transaction.objects.filter(uuid=transaction_id).first()
        if not transaction:
            logger.info(f"transaction {transaction_id} not found, skipping")
            return HttpResponseBadRequest("Transaction not found")
        if not transaction.fulfillment_identifier:
            logger.info(f"transaction {transaction_id} has no fulfillment uuid, skipping")
            return HttpResponseBadRequest("Transaction has no associated platform fulfillment identifier")

        try:
            EnterpriseApiClient().cancel_fulfillment(transaction.fulfillment_identifier)
        except requests.exceptions.HTTPError as exc:
            error_msg = f"Error canceling platform fulfillment {transaction.fulfillment_identifier}: {exc}"
            logger.exception(error_msg)
            return HttpResponseBadRequest(error_msg)

        url = reverse("admin:openedx_ledger_transaction_change", args=(transaction_id,))
        return HttpResponseRedirect(url)
