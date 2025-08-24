import reflex as rx

config = rx.Config(
    app_name="duck_ui",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)