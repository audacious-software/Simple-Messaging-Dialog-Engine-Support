/* global requirejs, $ */

requirejs.config({
  shim: {
    jquery: {
      exports: '$'
    },
    bootstrap: {
      deps: ['jquery']
    },
    cookie: {
      exports: 'Cookies'
    }
  },
  baseUrl: '/static/simple_dashboard/js/app',
  paths: {
    app: '/static/simple_dashboard/js/app',
    material: '/static/simple_dashboard/vendor/material-components-web.min',
    jquery: '/static/simple_dashboard/vendor/jquery',
    cookie: '/static/simple_dashboard/vendor/js.cookie',
  }
})

requirejs(['material', 'jquery', 'base'], function (mdc) {
  const select = mdc.select.MDCSelect.attachTo(document.querySelector('.mdc-select'))

  const url = URL.parse(window.location.href)

  if (url.searchParams.get('limit') !== null) {
    select.value = url.searchParams.get('limit')
  } else {
    select.value = '25'
  }

  select.listen('MDCSelect:change', () => {
    const url = URL.parse(window.location.href)
    url.searchParams.set('limit', select.value)
    window.location.href = url.href
  })

  mdc.dataTable.MDCDataTable.attachTo(document.getElementById('alerts_table'))

  $('.mdc-data-table__pagination-button').click(function (eventObj) {
    eventObj.preventDefault()

    const url = $(this).attr('data-url')

    window.location.href = url
  })
})
