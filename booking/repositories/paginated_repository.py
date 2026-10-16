from shared.contracts import Page


class PaginatedRepository:
    @staticmethod
    def page(queryset, page, mapper):
        count = queryset.count()
        page.check_count(count)
        items = [mapper(row) for row in queryset[page.offset : page.offset + page.size]]
        return Page(items=items, count=count, request=page)
