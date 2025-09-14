from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
import string
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
        parser.add_argument('--users', type=int, default=5, help='Number of random non-superuser accounts to ensure')
        parser.add_argument('--projects', type=int, default=12, help='Number of projects to create (may reuse existing titles)')
        parser.add_argument('--donations', type=int, default=40, help='Approximate number of donations to generate')
        parser.add_argument('--comments', type=int, default=60, help='Approximate number of top-level comments to generate')
        parser.add_argument('--max-replies', type=int, default=2, help='Maximum replies per top-level comment (random 0..max)')
        parser.add_argument('--flush-existing', action='store_true', help='Delete existing seeded domain data (projects/categories/tags/donations/comments/ratings) but keep users & superuser intact')

    def handle(self, *args, **options):
        project_count = options['projects']
        donation_target = options['donations']
        comment_target = options['comments']
        max_replies = max(0, options['max_replies'])
        user_target = options['users']
        flush = options['flush_existing']

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

        self.stdout.write(self.style.SUCCESS(
            "Seed complete:\n"
            f"  Users added: {len(created_users)} (total regular: {len(users)})\n"
            f"  Projects created: {len(created_projects)}\n"
            f"  Donations: {donation_created}\n"
            f"  Ratings: {rating_created}\n"
            f"  Top-level comments: {top_comments_created}\n"
            f"  Replies: {replies_created}"
        ))
