import markdown
import nh3

EXTENSIONS = ["fenced_code", "tables", "sane_lists", "nl2br"]
TAGS = nh3.ALLOWED_TAGS | {
    "img",
    "pre",
    "code",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
}
ATTRIBUTES = {
    **nh3.ALLOWED_ATTRIBUTES,
    "img": {"src", "alt", "title"},
    "code": {"class"},
}


def render(text):
    html = markdown.markdown(text, extensions=EXTENSIONS)
    return nh3.clean(
        html,
        tags=TAGS,
        attributes=ATTRIBUTES,
        link_rel="noopener noreferrer",
        set_tag_attribute_values={"a": {"target": "_blank"}},
    )
