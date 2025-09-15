from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from decimal import Decimal
import random
import string
import os
import io
from PIL import Image, ImageDraw, ImageFont
from projects.models import Category, Tag, Project, ProjectPicture, Donation, Comment, Rating

User = get_user_model()

WORDS = [
    "alpha","bravo","charlie","delta","eagle","forest","galaxy","horizon","ignite","jungle","kinetic","lunar","matrix","nebula","orbit","pulse","quantum","radar","sonic","terra","ultra","vector","wave","xeno","yonder","zen"  # simple pool
]

def random_word():
    return random.choice(WORDS)

def random_email():
    return f"{random_word()}{random.randint(100,999)}@example.com"

def random_name():
    first = random_word().capitalize()
    last = random_word().capitalize()
    return first, last

class Command(BaseCommand):
    help = "Seed sample users, categories, tags, projects, and donations for local development (idempotent-ish)."

    def add_arguments(self, parser):
        """Register CLI arguments for the seed command."""
        # Core quantities
        parser.add_argument('--users', type=int, default=5, help='Number of random non-superuser accounts to ensure')
        parser.add_argument('--projects', type=int, default=12, help='Number of projects to create (may reuse existing titles)')
        parser.add_argument('--donations', type=int, default=40, help='Approximate number of donations to generate')
        parser.add_argument('--comments', type=int, default=60, help='Approximate number of top-level comments to generate')
        parser.add_argument('--max-replies', type=int, default=2, help='Maximum replies per top-level comment (random 0..max)')
        parser.add_argument('--flush-existing', action='store_true', help='Delete existing seeded domain data (projects/categories/tags/donations/comments/ratings) but keep users & superuser intact')
        # Images
        parser.add_argument('--with-images', action='store_true', help='Generate profile pictures & project pictures if missing')
        parser.add_argument('--force-images', action='store_true', help='Regenerate images even if already set/created')
        parser.add_argument('--project-images-min', type=int, default=1, help='Minimum project images to ensure per project when using --with-images')
        parser.add_argument('--project-images-max', type=int, default=3, help='Maximum project images to ensure per project when using --with-images')

    def handle(self, *args, **options):
        project_count = options['projects']
        donation_target = options['donations']
        comment_target = options['comments']
        max_replies = max(0, options['max_replies'])
        user_target = options['users']
        flush = options['flush_existing']
        with_images = options['with_images']
        force_images = options['force_images']
        pimg_min = max(0, options['project_images_min'])
        pimg_max = max(pimg_min, options['project_images_max'])

        # Pre-calc media root
        from django.conf import settings
        media_root = settings.MEDIA_ROOT
        os.makedirs(os.path.join(media_root, 'profile_pictures'), exist_ok=True)
        os.makedirs(os.path.join(media_root, 'project_pictures'), exist_ok=True)

        def random_bg_color():
            # Avoid too-dark backgrounds
            return tuple(random.randint(60, 200) for _ in range(3))

        def make_text_image(text: str, size=(256, 256), font_size=96):
            img = Image.new('RGB', size, random_bg_color())
            draw = ImageDraw.Draw(img)
            try:
                # Attempt to load a common font; fallback gracefully
                font = ImageFont.truetype('arial.ttf', font_size)
            except Exception:
                font = ImageFont.load_default()
            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pos = ((size[0] - tw) / 2, (size[1] - th) / 2 - 5)
            draw.text(pos, text, fill='white', font=font)
            return img

        def make_project_banner(text: str, size=(800, 450)):
            img = Image.new('RGB', size, random_bg_color())
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype('arial.ttf', 40)
            except Exception:
                font = ImageFont.load_default()
            display = (text[:40] + '…') if len(text) > 40 else text
            bbox = draw.textbbox((0, 0), display, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pos = ((size[0] - tw) / 2, (size[1] - th) / 2 - 10)
            draw.text(pos, display, fill='white', font=font)
            return img

        if flush:
            self.stdout.write(self.style.WARNING('Flushing existing projects/categories/tags/donations'))
            Rating.objects.all().delete()
            Comment.objects.all().delete()
            Donation.objects.all().delete()
            ProjectPicture.objects.all().delete()
            Project.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()

        # Ensure baseline random users (exclude superusers already there)
        existing_regular = User.objects.filter(is_superuser=False).count()
        to_create = max(0, user_target - existing_regular)
        created_users = []
        for _ in range(to_create):
            email = random_email()
            first, last = random_name()
            # Required fields for custom user: username, email, mobile_phone
            # Generate a pseudo-Egyptian mobile number (matches validator ^01[0-2,5][0-9]{8}$)
            prefix = random.choice(['010', '011', '012', '015'])
            mobile = prefix + ''.join(random.choices(string.digits, k=8))
            username = email.split('@')[0]
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=first,
                last_name=last,
                mobile_phone=mobile,
            )
            created_users.append(user)
        # Refresh user list after creation
        users = list(User.objects.filter(is_superuser=False))
        if len(users) < 1:
            self.stderr.write('No regular users exist (superusers are skipped). Aborting.')
            return

        # Categories
        category_names = ['Technology', 'Art', 'Health', 'Education', 'Environment']
        categories = []
        for name in category_names:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': f'{name} related projects'})
            categories.append(cat)

        # Tags
        tag_names = ['open-source', 'community', 'innovation', 'sustainability', 'ai', 'design']
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)

        created_projects = []
        for i in range(project_count):
            creator = random.choice(users)
            category = random.choice(categories)
            start = timezone.now() - timezone.timedelta(days=random.randint(0, 5))
            end = start + timezone.timedelta(days=random.randint(10, 40))
            total_target = Decimal(random.choice([1000, 2500, 5000, 7500, 10000]))
            title = f"Sample Project {i+1}"  # deterministic label allows idempotent-ish reruns
            project, created = Project.objects.get_or_create(
                title=title,
                defaults={
                    'details': 'This is a seeded sample project used for local testing.',
                    'category': category,
                    'total_target': total_target,
                    'start_time': start,
                    'end_time': end,
                    'creator': creator,
                    'is_featured': random.choice([True, False]),
                }
            )
            if not project.slug:
                project.save()  # trigger slug assignment
            if created:
                for tag in random.sample(tags, random.randint(2, min(4, len(tags)))):
                    project.tags.add(tag)
                created_projects.append(project)

        # Donations (random spread)
        all_projects = list(Project.objects.all())
        donation_created = 0
        for _ in range(donation_target):
            p = random.choice(all_projects)
            donor = random.choice(users)
            amount = Decimal(random.choice([10, 25, 50, 75, 100, 150]))
            Donation.objects.create(project=p, user=donor, amount=amount)
            donation_created += 1

        # Ratings (each user rates random subset of projects, skipping own project)
        rating_created = 0
        for p in all_projects:
            raters = random.sample(users, k=min(len(users), random.randint(1, len(users))))
            for u in raters:
                if u.id == p.creator_id:
                    continue
                value = random.randint(3,5)  # bias toward positive
                Rating.objects.update_or_create(project=p, user=u, defaults={'value': value})
                rating_created += 1

        # Comments & replies
        sample_comments = [
            "Amazing concept!",
            "I like where this is going.",
            "Can you clarify the timeline?",
            "What tech stack are you using?",
            "This could really help a lot of people.",
            "How will funds be allocated?",
            "Following the progress eagerly!",
            "Great team behind this project.",
            "Is there an early backer perk?",
            "Love the sustainability angle." 
        ]
        top_comments_created = 0
        replies_created = 0
        for _ in range(comment_target):
            p = random.choice(all_projects)
            author = random.choice(users)
            text = random.choice(sample_comments)
            c = Comment.objects.create(project=p, user=author, content=text)
            top_comments_created += 1
            # Replies (0..max_replies)
            if max_replies > 0:
                for _r in range(random.randint(0, max_replies)):
                    replier = random.choice(users)
                    if replier == author and random.random() < 0.5:
                        # sometimes same author replies (simulate clarifications)
                        pass
                    reply_text = random.choice(sample_comments)
                    Comment.objects.create(project=p, user=replier, content=reply_text, parent=c)
                    replies_created += 1

        user_images_generated = 0
        project_images_generated = 0

        if with_images:
            # Profile pictures
            for user in users:
                needs = force_images or (not user.profile_picture or user.profile_picture.name.endswith('default.png'))
                if not needs:
                    continue
                initials = ''.join([user.first_name[:1] or 'U', user.last_name[:1] or 'X']).upper()
                img = make_text_image(initials)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                filename = f"avatar_{user.id}.png"
                user.profile_picture.save(filename, ContentFile(buf.read()), save=True)
                user_images_generated += 1

            # Project pictures
            for project in Project.objects.all():
                existing = project.pictures.count()
                target = random.randint(pimg_min, pimg_max) if pimg_max > 0 else 0
                if force_images:
                    # Delete existing and recreate
                    project.pictures.all().delete()
                    existing = 0
                to_add = max(0, target - existing)
                for idx in range(to_add):
                    banner = make_project_banner(project.title)
                    buf = io.BytesIO()
                    banner.save(buf, format='PNG')
                    buf.seek(0)
                    fname = f"project_{project.id}_{idx+1}.png"
                    pic = ProjectPicture(project=project)
                    pic.image.save(fname, ContentFile(buf.read()), save=True)
                    project_images_generated += 1

        self.stdout.write(self.style.SUCCESS(
            "Seed complete:\n"
            f"  Users added: {len(created_users)} (total regular: {len(users)})\n"
            f"  Projects created: {len(created_projects)}\n"
            f"  Donations: {donation_created}\n"
            f"  Ratings: {rating_created}\n"
            f"  Top-level comments: {top_comments_created}\n"
            f"  Replies: {replies_created}\n"
            f"  User images generated: {user_images_generated}\n"
            f"  Project images generated: {project_images_generated}"
        ))
