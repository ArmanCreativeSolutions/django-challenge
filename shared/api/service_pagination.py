from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from shared.contracts import PageRequest


class ServicePagination(PageNumberPagination):
    page_size = 50

    def get_page_request(self, request):
        self.request = request
        try:
            number = int(request.query_params.get(self.page_query_param, "1"))
        except (ValueError, TypeError) as exc:
            raise NotFound("Invalid page.") from exc
        return PageRequest(number=number, size=self.page_size)

    def respond(self, page, data):
        url = self.request.build_absolute_uri()
        number = page.request.number
        next_url = (
            replace_query_param(url, self.page_query_param, number + 1)
            if number * page.request.size < page.count
            else None
        )
        previous_url = None
        if number > 1:
            previous_url = (
                remove_query_param(url, self.page_query_param)
                if number == 2
                else replace_query_param(url, self.page_query_param, number - 1)
            )
        return Response(
            {"count": page.count, "next": next_url, "previous": previous_url, "results": data}
        )
