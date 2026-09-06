# Design System

The UI is deliberately minimal: server-rendered Django templates styled by
[Pico.css](https://picocss.com/) with a small project stylesheet on top.

## Foundations

- **Pico.css via CDN**, loaded once in the base template:
  `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">`.
- Lean on Pico's classless defaults — semantic HTML (`<nav>`, `<article>`,
  `<table>`, `<form>`, `<button>`) is styled without adding classes.
- Project overrides live in `chores/static/chores/style.css`, loaded after Pico.
  Keep it small; add a rule only when Pico has no answer.

## Layout

- One base template (`chores/templates/chores/base.html`) with a `<main
  class="container">` wrapper and a `{% block content %}`.
- Header partial: app name on the left, current member + "switch" link on the
  right. Shown on every page once a member is selected.
- Primary nav: Chores (list), Add chore, History.

## Components

- **Chore list** — a `<table>`: chore name, assignee, due date, actions.
- **Overdue flag** — add `class="overdue"` to the row; style in `style.css` as a
  left border / muted-red background plus an "Overdue" `<mark>` badge next to the
  due date. Never rely on colour alone — always include the text badge.
- **Actions** — "Done" and "Reassign" are `<form method="post">` submits, not
  links. "Done" is a primary button; "Reassign" is a `class="secondary"` button
  or inline `<select>`.
- **Forms** — plain Pico form markup, one field per row, labels above inputs,
  errors rendered under the field via `{{ form.field.errors }}`.
- **Flash messages** — Django `messages` framework rendered as Pico
  `<article>` blocks at the top of `content`.

## Conventions

- Mobile-first; the single `container` column is enough — no custom grid.
- Dates display as `M j, Y` (e.g. "Sep 6, 2026"); inputs use `<input type="date">`.
- No JavaScript in v1. If a later task needs interactivity, raise it before
  adding a framework.
- No custom web fonts, icon packs, or colour palette beyond the overdue accent.
