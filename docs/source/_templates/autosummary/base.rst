{% if fullname in repeated_titles -%}
{{ fullname.split(".", 1)[1] | escape | underline }}
{%- else -%}
{{ objname | escape | underline }}
{%- endif %}

``from {{ module }} import {{ objname }}``

.. currentmodule:: {{ module }}

.. auto{{ objtype }}:: {{ objname }}
