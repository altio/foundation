from django.template.defaultfilters import register


@register.filter
def cell_count(inline_form):
    """Returns the number of cells used in a tabular inline"""
    count = 1  # Hidden cell with hidden 'id' field
    for fieldset in inline_form:
        # Loop through all the fields (one per cell)
        for line in fieldset:
            for _ in line:
                count += 1
    if inline_form.formset.can_delete:
        # Delete checkbox
        count += 1
    return count
