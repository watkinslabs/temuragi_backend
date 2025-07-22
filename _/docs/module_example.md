# Example Module – `sample`  … fully featured template

```
app/
└─ _system/
   └─ sample/
      ├─ __init__.py
      ├─ view.py
      ├─ hook.py
      ├─ sample_model.py
      ├─ tpl/
      │  └─ sample/
      │     ├─ home.html
      │     └─ fragments/
      │        └─ item_row.html
      ├─ static/
      │  ├─ css/
      │  │  └─ sample.css
      │  └─ js/
      │     └─ sample.js
      └─ tests/
         └─ test_sample.py
```

---

### **init**.py

```python
"""sample module"""
```

### view\.py

```python
from flask import Blueprint, render_template, jsonify, request

bp = Blueprint(
    "sample",
    __name__,
    url_prefix="/sample",
    template_folder="tpl",
    static_folder="static",
)

@bp.route("/")
def home():
    """Render main page."""
    return render_template("sample/home.html")

@bp.route("/data", methods=["POST"])
def data_ajax():
    """AJAX endpoint returning JSON list."""
    payload = request.get_json(silent=True) or {}
    items = [{"id": i, "name": f"Item {i}"} for i in range(1, 6)]
    return jsonify(items=items, echo=payload)
```

### hook.py

```python
from flask import current_app, g

def register_sample_hooks(app):
    """Example before_request hook for logging."""
    @app.before_request
    def sample_log():
        if request.path.startswith("/sample"):
            current_app.logger.debug("sample module accessed… user=%s", g.get("user_id"))
```

### sample\_model.py

```python
import uuid
from sqlalchemy import Column, String
from app._system._core.base import BaseModel

class SampleItem(BaseModel):
    __tablename__ = "sample_items"
    name = Column(String, nullable=False)
```

### tpl/sample/home.html

```jinja
{% extends active_page_path %}

{% block page_title %}Sample Module{% endblock %}

{% block content %}
<div class="container py-4">
  <h1 class="mb-3"><i class="fa fa-flask me-2"></i>Sample Module</h1>
  <table class="table table-striped" id="item-table">
    <thead><tr><th>#</th><th>Name</th></tr></thead>
    <tbody></tbody>
  </table>
</div>
<script src="{{ url_for('sample.static', filename='js/sample.js') }}"></script>
{% endblock %}
```

### tpl/sample/fragments/item\_row\.html

```jinja
<tr>
  <td>{{ item.id }}</td>
  <td>{{ item.name }}</td>
</tr>
```

### static/css/sample.css

```css
/* sample module styles */
```

### static/js/sample.js

```javascript
$(function () {
  $.ajax({
    url: "/v2/sample/data",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ foo: "bar" }),
    success: function (resp) {
      const tbody = $("#item-table tbody");
      resp.items.forEach(function (item) {
        tbody.append(`{% include 'sample/fragments/item_row.html' %}`.replace("{{ item.id }}", item.id).replace("{{ item.name }}", item.name));
      });
    },
  });
});
```

### tests/test\_sample.py

```python
from flask.testing import FlaskClient

def test_home(client: FlaskClient):
    resp = client.get("/v2/sample/")
    assert resp.status_code == 200
```

---

Ready to copy into the repository…
