from django.test import TestCase, Client
from django.urls import reverse
import sys


class SearchPageTests(TestCase):
    """Минимальные тесты страницы поиска"""
    
    def setUp(self):
        self.client = Client()
    
    def test_1_search_page_status_200(self):
        """Тест 1: Главная страница открывается"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        print(f"✅ ТЕСТ 1: Главная страница открывается (200 OK)")
    
    def test_2_search_page_uses_correct_template(self):
        """Тест 2: Используется правильный шаблон"""
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'core/search.html')
        print(f"✅ ТЕСТ 2: Используется шаблон core/search.html")
    
    def test_3_search_page_contains_map_container(self):
        """Тест 3: На странице есть контейнер для карты"""
        response = self.client.get('/')
        self.assertContains(response, '<div id="map">')
        print(f"✅ ТЕСТ 3: Контейнер карты <div id=\"map\"> найден")
    
    def test_4_search_page_contains_search_form(self):
        """Тест 4: На странице есть форма поиска"""
        response = self.client.get('/')
        self.assertContains(response, 'name="city"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, '<form')
        print(f"✅ ТЕСТ 4: Форма поиска содержит поля city, q и <form>")
    
    def test_5_search_page_contains_route_form(self):
        """Тест 5: На странице есть форма маршрута"""
        response = self.client.get('/')
        self.assertContains(response, 'id="route-form"')
        self.assertContains(response, 'Планирование пешего маршрута')
        print(f"✅ ТЕСТ 5: Форма маршрута найдена (id=\"route-form\")")


class RouteFormElementsTests(TestCase):
    """Тесты элементов формы маршрута"""
    
    def setUp(self):
        self.client = Client()
    
    def test_6_route_form_has_start_point_input(self):
        """Тест 6: Форма имеет поле начальной точки"""
        response = self.client.get('/')
        self.assertContains(response, 'id="start-point"')
        self.assertContains(response, 'placeholder="Введите адрес или место"')
        print(f"✅ ТЕСТ 6: Поле начальной точки найдено (id=\"start-point\")")
    
    
    def test_8_route_form_has_end_type_selector(self):
        """Тест 7: Форма имеет выбор типа конечной точки"""
        response = self.client.get('/')
        self.assertContains(response, 'id="end-type"')
        self.assertContains(response, 'Вернуться в начало')
        print(f"✅ ТЕСТ 7: Селектор типа конечной точки найден (id=\"end-type\")")
    
    def test_9_route_form_has_walking_time_select(self):
        """Тест 8: Форма имеет выбор времени прогулки"""
        response = self.client.get('/')
        self.assertContains(response, 'id="walking-time"')
        self.assertContains(response, '30 минут')
        print(f"✅ ТЕСТ 8: Селектор времени прогулки найден (id=\"walking-time\")")
    
    def test_10_route_form_has_category_checkboxes(self):
        """Тест 9: Форма имеет чекбоксы категорий"""
        response = self.client.get('/')
        self.assertContains(response, 'name="visit-category"')
        self.assertContains(response, 'Кафе')
        self.assertContains(response, 'Парки')
        print(f"✅ ТЕСТ 9: Чекбоксы категорий найдены (name=\"visit-category\")")


class JavaScriptTests(TestCase):
    """Тесты JavaScript функций на странице"""
    
    def setUp(self):
        self.client = Client()
    
    def test_11_page_contains_planRoute_function(self):
        """Тест 10: Функция planRoute() определена"""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        self.assertIn('function planRoute()', content)
        print(f"✅ ТЕСТ 10: JavaScript функция planRoute() определена")
    
    def test_12_page_contains_useCurrentLocation_function(self):
        """Тест 11: Функция useCurrentLocation() определена"""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        self.assertIn('function useCurrentLocation()', content)
        print(f"✅ ТЕСТ 11: JavaScript функция useCurrentLocation() определена")


class MapTests(TestCase):
    """Тесты карты 2GIS"""
    
    def setUp(self):
        self.client = Client()
    
    def test_16_page_has_map_initialization(self):
        """Тест 12: На странице есть инициализация карты"""
        response = self.client.get('/')
        self.assertContains(response, 'DG.map')
        print(f"✅ ТЕСТ 12: Инициализация карты (DG.map) найдена")
    
    def test_17_page_has_map_click_handler(self):
        """Тест 13: На странице есть обработчик клика по карте"""
        response = self.client.get('/')
        self.assertContains(response, 'map.on')
        print(f"✅ ТЕСТ 14: Обработчик клика по карте (map.on) найден")
    
    def test_18_page_has_route_buttons(self):
        """Тест 15: На странице есть кнопки маршрута"""
        response = self.client.get('/')
        self.assertContains(response, 'Построить маршрут')
        self.assertContains(response, 'Сохранить маршрут')
        print(f"✅ ТЕСТ 15: Кнопка \"Построить маршрут\" найдена")
        print(f"✅ ТЕСТ 15: Кнопка \"Сохранить маршрут\" найдена")
    
    
    def test_20_page_has_route_info_container(self):
        """Тест 16: На странице есть контейнер для информации о маршруте"""
        response = self.client.get('/')
        self.assertContains(response, 'id="route-info"')
        self.assertContains(response, 'id="route-details"')
        print(f"✅ ТЕСТ 16: Контейнер информации о маршруте найден (id=\"route-info\")")
