from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(db_index=True, unique=True)),
                ("name", models.CharField(max_length=80, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(db_index=True, unique=True)),
                ("title", models.CharField(max_length=240)),
                ("summary", models.TextField(blank=True)),
                ("body_html", models.TextField()),
                ("date", models.DateField(db_index=True)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
            ],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.AddField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="posts", to="pages.tag"),
        ),
    ]
