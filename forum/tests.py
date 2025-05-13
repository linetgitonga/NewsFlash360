from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Post, Comment, Tag

User = get_user_model()


class ForumModelTests(TestCase):
    """Tests for forum models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test comment'
        )
        
        self.tag = Tag.objects.create(name='TestTag')
        self.post.tags.add(self.tag)
    
    def test_category_creation(self):
        """Test category creation and string representation"""
        self.assertEqual(str(self.category), 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
    
    def test_post_creation(self):
        """Test post creation and string representation"""
        self.assertEqual(str(self.post), 'Test Post')
        self.assertEqual(self.post.slug, 'test-post')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.status, 'published')
        self.assertIsNotNone(self.post.published_at)
    
    def test_comment_creation(self):
        """Test comment creation and string representation"""
        self.assertTrue(str(self.comment).startswith('Comment by testuser on'))
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.post, self.post)
        self.assertTrue(self.comment.active)
    
    def test_tag_creation(self):
        """Test tag creation and relationship with post"""
        self.assertEqual(str(self.tag), 'TestTag')
        self.assertEqual(self.tag.slug, 'testtag')
        self.assertIn(self.post, self.tag.posts.all())
        self.assertIn(self.tag, self.post.tags.all())


class ForumAPITests(APITestCase):
    """Tests for forum API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test comment'
        )
        
        self.tag = Tag.objects.create(name='TestTag')
        self.post.tags.add(self.tag)
    
    def test_post_list(self):
        """Test retrieving post list"""
        url = reverse('forum:post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_post_detail(self):
        """Test retrieving post detail"""
        url = reverse('forum:post-detail', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')
    
    def test_create_post_unauthorized(self):
        """Test creating post without authentication"""
        url = reverse('forum:post-list')
        data = {
            'title': 'New Post',
            'content': 'This is a new post',
            'category': self.category.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_post_authorized(self):
        """Test creating post with authentication"""
        self.client.force_authenticate(user=self.user)
        url = reverse('forum:post-list')
        data = {
            'title': 'New Post',
            'content': 'This is a new post',
            'category': self.category.id,
            'language': 'en'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_upvote_post(self):
        """Test upvoting a post"""
        self.client.force_authenticate(user=self.user)
        url = reverse('forum:post-upvote', args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.upvotes.count(), 1)
        
        # Test removing upvote
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.upvotes.count(), 0)
    
    def test_comment_list(self):
        """Test retrieving comment list"""
        url = reverse('forum:comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_create_comment(self):
        """Test creating a comment"""
        self.client.force_authenticate(user=self.user)
        url = reverse('forum:comment-list')
        data = {
            'post': self.post.id,
            'content': 'This is another test comment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
    
    def test_tag_list(self):
        """Test retrieving tag list"""
        url = reverse('forum:tag-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'TestTag')