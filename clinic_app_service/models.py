from django.utils import timezone
from django.db import models
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator

SEX_CHOICES = (
    ('man', 'Чоловіча'),
    ('female', 'Жіноча'),
)

BENEFIT_GROUP_CHOICES = (
    ('military', 'Військові (знижка 20%)'),
    ('elderly', 'Люди похилого віку (знижка 10%)'),
    ('disabled', 'Люди з інвалідністю (знижка 5%)'),
    ('staff_family', 'Члени родин працівників (знижка 40%)'),
)

USER_TYPE_CHOICES = (
    ('recorder', 'Реєстратор'),
    ('manager', 'Керівник'),
    ('doctor', 'Лікар'),
)

PRICE_LIST_STATUS_CHOICES = (
    ('active', 'Активний'),
    ('inactive', 'Неактивний'),
)

APPOINTMENT_STATUS_CHOICES = (
    ('planned', 'Запланований'),
    ('canceled', 'Скасований'),
    ('done', 'Завершений'),
)

APPOINTMENT_TIME_CHOICES = (
    ('8:00', '8:00 - 8:30'),
    ('8:30', '8:30 - 9:00'),
    ('9:00', '9:00 - 9:30'),
    ('9:30', '9:30 - 9:30'),
    ('10:00', '10:00 - 10:30'),
    ('10:30', '10:30 - 11:00'),
    ('11:00', '11:00 - 11:30'),
    ('11:30', '11:30 - 12:00'),
    ('12:00', '12:00 - 12:30'),
    ('12:30', '12:30 - 13:00'),
    ('13:00', '13:00 - 13:30'),
)

class Patient(models.Model):
    first_name = models.CharField("Ім'я", max_length=255, blank=False)
    last_name = models.CharField("Прізвище", max_length=255, blank=False)
    middle_name = models.CharField("По батькові", max_length=255, blank=True, default='')
    phone_number = models.CharField("Номер телефону", max_length=15, blank=False, unique=True)
    email = models.EmailField("Електронна пошта", max_length=255, blank=False, unique=True)
    birth_date = models.DateField("Дата народження", blank=False)
    gender = models.CharField("Стать", max_length=8, choices=SEX_CHOICES, blank=False)
    benefit_group = models.CharField("Пільгова група", max_length=50, choices=BENEFIT_GROUP_CHOICES, blank=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Service(models.Model):
    service_name = models.CharField("Назва послуги", max_length=100, unique=True)
    is_service_archived = models.BooleanField("Архівовано", blank=False, default=False)

    def __str__(self):
        return self.service_name

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = (
        ('analysis', 'Результати аналізів'),
        ('referral', 'Направлення'),
        ('diagnosis', 'Діагноз'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField("Тип запису", max_length=255, choices=RECORD_TYPE_CHOICES, null=False)

    pdf_links = models.CharField("Посилання на PDF-файли", max_length=255, blank=True)
    services = models.ManyToManyField(Service, verbose_name="Необхідні обстеження",
                                      related_name='medical_records', blank=False)
    doctor_conclusion = models.CharField("Висновок лікаря", max_length=255, blank=True)

    created_at = models.DateTimeField("Дата створення", blank=False, default=timezone.now)

    class Meta:
        constraints = [
            # Якщо record_type = 'diagnosis', то doctor_conclusion не може бути NULL
            CheckConstraint(
                check=Q(record_type='diagnosis') & ~Q(doctor_conclusion=None) |
                      ~Q(record_type='diagnosis'),
                name='check_diagnosis_doctor_conclusion'
            ),

            # Якщо record_type = 'analysis', то pdf_links не може бути NULL
            CheckConstraint(
                check=Q(record_type='analysis') & ~Q(pdf_links=None) |
                      ~Q(record_type='analysis'),
                name='check_analysis_pdf_links'
            ),
        ]
    # def save(self, *args, **kwargs):
    #     if self.record_type == 'referral' and not self.pk:  # Перевіряємо лише при створенні
    #         super().save(*args, **kwargs)  # Зберігаємо, щоб можна було додати ManyToMany
    #         if not self.services.exists():
    #             return  # Якщо немає послуг, не зберігаємо
    #     super().save(*args, **kwargs)
    def __str__(self):
        services_names = ", ".join(service.name for service in self.services.all())
        return f" {self.record_type} (Пацієнт: {self.patient}) {services_names}"


class Invoice(models.Model):
    discount_percent = models.IntegerField("Знижка", blank=True, null=True)
    subtotal = models.DecimalField("Сума без знижки", max_digits=12, decimal_places=2, blank=False)
    total = models.DecimalField("Сума зі знижкою", max_digits=12, decimal_places=2, blank=False)
    paid_date = models.DateTimeField("Дата оплати", blank=False, default=timezone.now)

    def __str__(self):
        return f"Invoice {self.pk}"

class User(models.Model):
    first_name = models.CharField("Ім'я", max_length=255, blank=False)
    last_name = models.CharField("Прізвище", max_length=255, blank=False)
    middle_name = models.CharField("По батькові", max_length=255, blank=True, default='')
    email = models.EmailField("Електронна пошта", max_length=255, blank=False, unique=True)
    user_type = models.CharField("Тип користувача", max_length=255, choices=USER_TYPE_CHOICES, blank=False)
    services = models.ManyToManyField(Service, verbose_name="Послуги",
                                      related_name='user_doctor', blank=True)
    password_hash = models.TextField("Хеш паролю", blank=False)
    qualification = models.CharField("Кваліфікація", max_length=255, blank=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Якщо користувач не лікар, видаляємо всі послуги
        if self.user_type != 'doctor':
            self.services.clear()

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

class PriceList(models.Model):

    name = models.CharField("Назва прайс-листу", max_length=255, blank=False)
    status = models.CharField("Стан", max_length=8, choices=PRICE_LIST_STATUS_CHOICES, default='Неактивний', blank=False)
    is_archived = models.BooleanField("Є архівованим", blank=False, default=False)
    archive_reason = models.TextField("Причина архівування", blank=True)

    def __str__(self):
        return f"Прайс-лист {self.pk} "

class PriceListEntry(models.Model):
    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='price_entries'
    )
    price = models.DecimalField("Вартість", max_digits=12, decimal_places=2,
                                default=0.01, blank=False, validators=[MinValueValidator(0.01)])

    def __str__(self):
        return f"Записи прайс-листа {self.pk}"

class Appointment(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments',
        blank=False
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'user_type': 'doctor'},
        blank=False
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='appointments',
        blank=False
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='appointments',
        blank=False
    )

    execution_status = models.CharField(
        "Стан виконання",
        max_length=15,
        choices=APPOINTMENT_STATUS_CHOICES,
        default='Заплановано',
        blank=False
    )
    appointment_date = models.DateTimeField("Дата проведення", blank=True, null=True)
    completion_date = models.DateTimeField("Дата виконання", blank=True, null=True)

    def __str__(self):
        return (f"Прийом #{self.pk} | Пацієнт: {self.patient} | "
                f"Лікар: {self.doctor} | Послуга: {self.service.name}")
