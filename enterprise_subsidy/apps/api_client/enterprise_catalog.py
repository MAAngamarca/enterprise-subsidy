"""
Enterprise Catalog api client for the subsidy service.
"""
import logging
from urllib.parse import urljoin

import requests
from django.conf import settings

from enterprise_subsidy.apps.api_client.base_oauth import ApiClientException, BaseOAuthClient
from enterprise_subsidy.apps.subsidy.constants import (
    EDX_PRODUCT_SOURCE,
    EDX_VERIFIED_COURSE_MODE,
    EXECUTIVE_EDUCATION_MODE
)

logger = logging.getLogger(__name__)


class EnterpriseCatalogApiClient(BaseOAuthClient):
    """
    API client for calls to the enterprise service.
    """
    api_base_url = urljoin(settings.ENTERPRISE_CATALOG_URL, 'api/v1/')
    enterprise_customer_endpoint = urljoin(api_base_url, 'enterprise-customer/')

    def enterprise_customer_url(self, enterprise_customer_uuid):
        return urljoin(
            self.enterprise_customer_endpoint,
            f"{enterprise_customer_uuid}/",
        )

    def content_metadata_url(self, enterprise_customer_uuid, content_identifier):
        return urljoin(
            self.enterprise_customer_url(enterprise_customer_uuid),
            f'content-metadata/{content_identifier}/'
        )

    def get_product_source(self, enterprise_customer_uuid, content_identifier):
        """
        Returns the a specific piece of content's product source as it's defined within the content metadata of the
        Enterprise Catalog service.

        Arguments:
            enterprise_customer_uuid (UUID): UUID of the customer associated with an enterprise
            content_identifier (str): **Either** the content UUID or content key identifier for a content record.
                Note: the content needs to be owned by a catalog associated with the provided customer else this
                method will throw an HTTPError.
        Returns:
            Either `2U` or `edX` based on the content's product source content metadata field
        Raises:
            requests.exceptions.HTTPError: if service is down/unavailable or status code comes back >= 300,
            the method will log and throw an HTTPError exception. A 404 exception will be thrown if the content
            does not exist, or is not present in a catalog associated with the customer.
        """
        course_details = self.get_content_metadata_for_customer(enterprise_customer_uuid, content_identifier)
        if product_source := course_details.get('product_source'):
            return product_source
        return EDX_PRODUCT_SOURCE

    def get_course_price(self, enterprise_customer_uuid, content_identifier):
        """
        Returns the price of a content as it's defined within the entitlements of the Enterprise Catalog's content
        metadata record for a piece of content.

        Arguments:
            enterprise_customer_uuid (UUID): UUID of the customer associated with an enterprise
            content_identifier (str): **Either** the content UUID or content key identifier for a content record.
                Note: the content needs to be owned by a catalog associated with the provided customer else this
                method will throw an HTTPError.
        Returns:
            Pricing (list of dicts): Array containing mappings of an individual content's course price associated with
            a each of it's course mode
        Raises:
            requests.exceptions.HTTPError: if service is down/unavailable or status code comes back >= 300,
            the method will log and throw an HTTPError exception. A 404 exception will be thrown if the content
            does not exist, or is not present in a catalog associated with the customer.
        """
        course_details = self.get_content_metadata_for_customer(enterprise_customer_uuid, content_identifier)
        source_mode = EXECUTIVE_EDUCATION_MODE if course_details.get('product_source') else EDX_VERIFIED_COURSE_MODE
        for entitlement in course_details.get('entitlements'):
            if entitlement.get('mode') == source_mode:
                return entitlement.get('price')
        raise ApiClientException(
            f'Missing content pricing mode: {source_mode} in content: {content_identifier} entitlements'
        )

    def get_content_metadata_for_customer(self, enterprise_customer_uuid, content_identifier):
        """
        Returns Enterprise Customer related data for a specified piece on content.

        Arguments:
            enterprise_customer_uuid (UUID): UUID of the customer associated with an enterprise
            content_identifier (str): **Either** the content UUID or content key identifier for a content record.
                Note: the content needs to be owned by a catalog associated with the provided customer else this
                method will throw an HTTPError.
        Returns:
            response (dict): JSON response object associated with a content metadata record
        Raises:
            requests.exceptions.HTTPError: if service is down/unavailable or status code comes back >= 300,
            the method will log and throw an HTTPError exception. A 404 exception will be thrown if the content
            does not exist, or is not present in a catalog associated with the customer.
        """
        content_metadata_url = self.content_metadata_url(enterprise_customer_uuid, content_identifier)
        try:
            response = self.client.get(content_metadata_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            if hasattr(response, 'text'):
                logger.error(
                    f'Failed to fetch enterprise customer data for {enterprise_customer_uuid} because {response.text}',
                )
            raise exc
