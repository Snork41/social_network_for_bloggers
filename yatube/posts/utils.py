from django.core.paginator import Paginator

from yatube.settings import AMOUNT_POSTS


def get_page(request, post_list):
    paginator = Paginator(post_list, AMOUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
