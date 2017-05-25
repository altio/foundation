from __future__ import unicode_literals

from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..backend.views.controller import ALL_VAR, PAGE_VAR

register = Library()

DOT = '.'


@register.simple_tag
def paginator_number(view, i):
    """
    Generates an individual page index link in a paginated list.
    """
    if i == DOT:
        return '... '
    elif i == view.page.number:
        return format_html('<li class="active"><a class="this-page" href="#">{} <span class="sr-only">(current)</span></a></li> ', i)
    else:
        return format_html('<li><a href="{}"{}>{}</a></li> ',
                           view.get_query_string({PAGE_VAR: i}),
                           mark_safe(' class="end"' if i == view.page.paginator.num_pages - 1 else ''),
                           i)


@register.inclusion_tag('fragments/pagination.html')
def pagination(view):
    """
    Generates the series of links to the pages in a paginated list.
    """
    paginator, page, page_num = view.paginator, None, 1
    previous_page = next_page = None

    # pagination_required = (not cl.show_all or not cl.can_show_all) and cl.multi_page
    pagination_required = paginator.num_pages > 1
    if not pagination_required:
        page_range = []
    else:
        page, page_num = view.page, view.page.number
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 10:
            page_range = range(paginator.num_pages)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS + 1):
                page_range.extend(range(1, ON_ENDS + 1))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num))
            else:
                page_range.extend(range(1, page_num))
            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS):
                page_range.extend(range(page_num, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(range(paginator.num_pages - ON_ENDS + 1, paginator.num_pages + 1))
            else:
                page_range.extend(range(page_num, paginator.num_pages + 1))
        if page_num > 1:
            previous_page = view.get_query_string({PAGE_VAR: page_num - 1})
        if page_num < paginator.num_pages:
            next_page = view.get_query_string({PAGE_VAR: page_num + 1})

    # need_show_all_link = cl.can_show_all and not cl.show_all and cl.multi_page
    need_show_all_link = pagination_required
    return {
        'view': view,
        'pagination_required': pagination_required,
        'paginator': paginator,
        'previous_page': previous_page,
        'page': page,
        'next_page': next_page,
        'show_all_url': need_show_all_link and view.get_query_string({ALL_VAR: ''}),
        'page_range': page_range,
        'ALL_VAR': ALL_VAR,
        '1': 1,
    }
