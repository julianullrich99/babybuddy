if (typeof jQuery === "undefined") {
  throw new Error("Baby Buddy requires jQuery.");
}

/**
 * Baby Buddy Namespace
 *
 * Default namespace for the Baby Buddy app.
 *
 * @type {{}}
 */
var BabyBuddy = (function () {
  return {};
})();

/**
 * Pull to refresh.
 *
 * @type {{init: BabyBuddy.PullToRefresh.init, onRefresh: BabyBuddy.PullToRefresh.onRefresh}}
 */
BabyBuddy.PullToRefresh = (function (ptr) {
  return {
    init: function () {
      ptr.init({
        mainElement: "body",
        onRefresh: this.onRefresh,
      });
    },

    onRefresh: function () {
      window.location.reload();
    },
  };
})(PullToRefresh);

/**
 * Show a loading spinner on the submit button when a form is submitted and
 * prevent double-submission.
 */
(function handleFormSubmit() {
  $("form").on("submit", function (event) {
    var submitter =
      (event.originalEvent && event.originalEvent.submitter) ||
      $(this).find('[type="submit"]')[0];
    if (!submitter || $(submitter).prop("disabled")) return;
    $(submitter)
      .prop("disabled", true)
      .prepend(
        '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>',
      );
  });
})();

BabyBuddy.RememberAdvancedToggle = function (ptr) {
  localStorage.setItem("advancedForm", event.newState);
};

(function toggleAdvancedFields() {
  window.addEventListener("load", function () {
    if (localStorage.getItem("advancedForm") !== "open") {
      return;
    }

    document.querySelectorAll(".advanced-fields").forEach(function (node) {
      node.open = true;
    });
  });
})();

/* Dashboard card ordering
 *
 * Drives the move up/down controls in user settings. Reordering happens in the
 * DOM; the resulting order is written back to a hidden input so it submits with
 * the rest of the settings form.
 */
(function dashboardCardOrder() {
  function updateValue(list) {
    var value = Array.prototype.map
      .call(
        list.querySelectorAll(".dashboard-card-order__item"),
        function (item) {
          return item.dataset.cardId;
        },
      )
      .join(",");
    var input = document.querySelector(".dashboard-card-order__value");
    if (input) {
      input.value = value;
    }
  }

  function move(button) {
    var item = button.closest(".dashboard-card-order__item");
    var list = item.parentNode;
    if (button.dataset.cardMove === "up") {
      var previous = item.previousElementSibling;
      if (!previous) {
        return;
      }
      list.insertBefore(item, previous);
    } else {
      var next = item.nextElementSibling;
      if (!next) {
        return;
      }
      list.insertBefore(next, item);
    }
    updateValue(list);
    // Keep focus on the control so a card can be moved several places without
    // reaching for the mouse again.
    button.focus();
  }

  window.addEventListener("load", function () {
    var list = document.querySelector(".dashboard-card-order");
    if (!list) {
      return;
    }
    updateValue(list);
    list.addEventListener("click", function (event) {
      var button = event.target.closest("[data-card-move]");
      if (button) {
        move(button);
      }
    });
  });
})();
