---
layout: page
permalink: /cv/
title: CV
nav: true
nav_order: 4
---

{% assign cv_pdf = site.data.socials.cv.url | relative_url %}

<p>
  <a class="btn btn-sm z-depth-0" href="{{ cv_pdf }}" target="_blank" rel="noopener">
    <i class="fa-solid fa-file-pdf"></i> Download PDF
  </a>
</p>

<object data="{{ cv_pdf }}" type="application/pdf" width="100%" style="height: 85vh; min-height: 600px;" aria-label="Curriculum vitae of Michael T. Saban">
  <p>Your browser can't display the PDF here. <a href="{{ cv_pdf }}">Download the CV</a> instead.</p>
</object>
