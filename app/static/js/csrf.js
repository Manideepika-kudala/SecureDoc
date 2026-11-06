(function () {
    const originalFetch = window.fetch.bind(window);

    window.fetch = function (input, init = {}) {
        const requestUrl = input instanceof Request ? input.url : input;
        const url = new URL(requestUrl, window.location.href);
        const method = (
            init.method ||
            (input instanceof Request ? input.method : "GET")
        ).toUpperCase();

        if (
            url.origin === window.location.origin &&
            !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)
        ) {
            const cookie = document.cookie
                .split("; ")
                .find(item => item.startsWith("csrf_token="));

            if (cookie) {
                const token = decodeURIComponent(cookie.substring("csrf_token=".length));
                const headers = new Headers(
                    init.headers ||
                    (input instanceof Request ? input.headers : undefined)
                );

                headers.set("X-CSRF-Token", token);
                init = { ...init, headers };
            }
        }

        return originalFetch(input, init);
    };
})();
