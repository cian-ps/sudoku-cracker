from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from random import randint
from typing import Any

_select_code: int | None = None
_on_selection: Callable[[Sequence[str]], None] | None = None


def open_image_file(
    *,
    on_selection: Callable[[Sequence[str]], None],
    **_kwargs: object,
) -> None:
    """Open the system image picker and return the selected content URI."""
    from android import activity, mActivity
    from jnius import autoclass, cast

    global _select_code, _on_selection

    String = autoclass("java.lang.String")
    Intent = autoclass("android.content.Intent")

    activity.unbind(on_activity_result=_on_activity_result)
    _on_selection = on_selection
    _select_code = randint(123456, 654321)
    activity.bind(on_activity_result=_on_activity_result)

    intent = Intent(Intent.ACTION_GET_CONTENT)
    intent.setType("image/*")
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    mActivity.startActivityForResult(
        Intent.createChooser(
            intent,
            cast("java.lang.CharSequence", String("Select image")),
        ),
        _select_code,
    )


def _on_activity_result(request_code: int, result_code: int, data: Any) -> None:
    from android import activity
    from jnius import autoclass

    Activity = autoclass("android.app.Activity")

    if _select_code is None or _on_selection is None:
        return
    if request_code != _select_code:
        return

    activity.unbind(on_activity_result=_on_activity_result)
    callback = _on_selection
    _clear_picker_state()

    if data is None or result_code != Activity.RESULT_OK:
        callback([])
        return

    uri = data.getData()
    if uri is None:
        logging.warning("Image picker returned no URI")
        callback([])
        return

    uri_str = str(uri.toString())
    logging.info("Image picker selected %s", uri_str)
    callback([uri_str])


def _clear_picker_state() -> None:
    global _select_code, _on_selection
    _select_code = None
    _on_selection = None
