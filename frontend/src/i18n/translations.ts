export type Language = 'ar' | 'en'

type Dict = Record<string, { ar: string; en: string }>

// Keyed by page/section. Covers the surfaces a first-look demo actually
// touches (landing, auth, nav, settings, dashboard headline). The rest of
// the product is still Arabic-only — real translation of every page is a
// separate, larger pass.
export const translations: Dict = {
  // HomePage
  'home.kicker': { ar: 'منصة واحدة لفريق الطفل كله', en: 'One platform for the whole care team' },
  'home.h1.part1': { ar: 'رحلة طفلك تستحق أن تُرى', en: "Your child's journey deserves to be seen" },
  'home.h1.part2': { ar: 'كاملة.', en: 'fully.' },
  'home.cta.register': { ar: 'إنشاء حساب جديد', en: 'Create account' },
  'home.cta.login': { ar: 'تسجيل الدخول', en: 'Sign in' },
  'home.privacy': { ar: '🛡️ بيانات آمنة ومحمية • ولي الأمر يتحكم بالصلاحيات', en: '🛡️ Private by design • guardians control access' },
  'home.benefit.reports': { ar: 'تقارير موحدة', en: 'Unified reports' },
  'home.benefit.goals': { ar: 'أهداف واضحة', en: 'Clear goals' },
  'home.benefit.team': { ar: 'فريق مترابط', en: 'Connected team' },
  'nav.login': { ar: 'تسجيل الدخول', en: 'Sign in' },
  'nav.register': { ar: 'إنشاء حساب', en: 'Create account' },

  // LoginPage
  'login.kicker': { ar: 'تسجيل الدخول', en: 'Sign in' },
  'login.title': { ar: 'أهلًا بك في وئام', en: 'Welcome to Weam' },
  'login.subtitle': { ar: 'أدخلي بيانات حسابك للمتابعة.', en: 'Enter your details to continue.' },
  'login.email': { ar: 'البريد الإلكتروني', en: 'Email' },
  'login.password': { ar: 'كلمة المرور', en: 'Password' },
  'login.submit': { ar: 'تسجيل الدخول', en: 'Sign in' },
  'login.submitting': { ar: 'جاري الدخول...', en: 'Signing in...' },
  'login.or': { ar: 'أو', en: 'or' },
  'login.noAccount': { ar: 'ما عندك حساب؟', en: "Don't have an account?" },
  'login.createOne': { ar: 'إنشاء حساب جديد', en: 'Create one' },
  'login.backHome': { ar: 'العودة إلى البداية', en: 'Back to home' },
  'login.tagline': { ar: 'كل فريق الطفل في مساحة واحدة.', en: "Your child's whole team, in one place." },
  'login.demoNote': { ar: 'نسخة المسابقة تستخدم بيانات تجريبية فقط.', en: 'This hackathon build uses demo data only.' },

  // RegisterPage
  'register.haveAccount': { ar: 'لديك حساب؟', en: 'Already have an account?' },
  'register.signIn': { ar: 'تسجيل الدخول', en: 'Sign in' },
  'register.kicker': { ar: 'ابدئي بخطوة بسيطة', en: 'Start with one simple step' },
  'register.title': { ar: 'إنشاء حساب وئام', en: 'Create your Weam account' },
  'register.subtitle': { ar: 'اختاري نوع الحساب، وبعدها نكمل المعلومات اللازمة فقط.', en: "Choose your account type, then we'll ask only what's needed." },
  'register.role.guardian': { ar: 'ولي أمر', en: 'Guardian' },
  'register.role.guardian.copy': { ar: 'إدارة ملفات الأطفال وفريق الرعاية', en: "Manage your child's profile and care team" },
  'register.role.provider': { ar: 'مقدم رعاية', en: 'Care provider' },
  'register.role.provider.copy': { ar: 'طبيب، أخصائي، معلم أو مقدم دعم', en: 'Doctor, specialist, teacher, or support provider' },
  'register.role.center': { ar: 'مركز', en: 'Center' },
  'register.role.center.copy': { ar: 'إدارة ملف المركز وخدماته ومختصيه', en: 'Manage the center profile, services, and specialists' },
  'register.fullName': { ar: 'الاسم الكامل', en: 'Full name' },
  'register.email': { ar: 'البريد الإلكتروني', en: 'Email' },
  'register.specialty': { ar: 'التخصص', en: 'Specialty' },
  'register.password': { ar: 'كلمة المرور', en: 'Password' },
  'register.submit': { ar: 'إنشاء الحساب', en: 'Create account' },
  'register.submitting': { ar: 'جاري إنشاء الحساب...', en: 'Creating account...' },
  'register.or': { ar: 'أو', en: 'or' },

  // Role labels
  'role.guardian': { ar: 'ولي أمر', en: 'Guardian' },
  'role.provider': { ar: 'مقدم رعاية', en: 'Care provider' },
  'role.center': { ar: 'حساب مركز', en: 'Center account' },
  'role.admin': { ar: 'إدارة وئام', en: 'Weam admin' },

  // AppShell nav
  'nav.home': { ar: 'الرئيسية', en: 'Home' },
  'nav.centers': { ar: 'المراكز والخدمات', en: 'Centers & Services' },
  'nav.provider': { ar: 'مساحة مقدم الخدمة', en: 'Provider space' },
  'nav.messages': { ar: 'الرسائل', en: 'Messages' },
  'nav.invitations': { ar: 'الدعوات', en: 'Invitations' },
  'nav.notifications': { ar: 'التنبيهات', en: 'Notifications' },
  'nav.addChild': { ar: 'إضافة طفل', en: 'Add child' },
  'nav.settings': { ar: 'الإعدادات', en: 'Settings' },
  'nav.admin': { ar: 'لوحة الإدارة', en: 'Admin dashboard' },
  'nav.signOut': { ar: 'تسجيل الخروج', en: 'Sign out' },
  'nav.privacyTitle': { ar: 'خصوصيتك أولويتنا', en: 'Your privacy comes first' },
  'nav.privacyBody': { ar: 'لا يظهر المحتوى إلا لمن يملك صلاحية فعالة.', en: 'Content is only visible to people with active permission.' },

  // SettingsPage
  'settings.kicker': { ar: 'الإعدادات', en: 'Settings' },
  'settings.title': { ar: 'تفضيلاتك في وئام', en: 'Your preferences' },
  'settings.subtitle': { ar: 'خصّصي مظهر التطبيق وحجم الخط بما يناسبك. هذه الإعدادات تُحفظ على جهازك فقط.', en: 'Customize the app appearance and text size. Saved to this device only.' },
  'settings.account': { ar: 'الحساب', en: 'Account' },
  'settings.accountSubtitle': { ar: 'معلومات حسابك الحالي.', en: 'Your current account details.' },
  'settings.name': { ar: 'الاسم', en: 'Name' },
  'settings.email': { ar: 'البريد الإلكتروني', en: 'Email' },
  'settings.appearance': { ar: 'المظهر', en: 'Appearance' },
  'settings.appearanceSubtitle': { ar: 'اختاري بين المظهر الفاتح والداكن، أو اتركيه يتبع إعداد جهازك.', en: 'Choose light or dark, or follow your device setting.' },
  'settings.theme.light': { ar: 'فاتح', en: 'Light' },
  'settings.theme.lightHint': { ar: 'مظهر فاتح دائمًا', en: 'Always light' },
  'settings.theme.dark': { ar: 'داكن', en: 'Dark' },
  'settings.theme.darkHint': { ar: 'مظهر داكن دائمًا', en: 'Always dark' },
  'settings.theme.system': { ar: 'حسب الجهاز', en: 'System' },
  'settings.theme.systemHint': { ar: 'يتبع إعداد جهازك تلقائيًا', en: "Follows your device automatically" },
  'settings.textSize': { ar: 'حجم النص والأيقونات', en: 'Text & icon size' },
  'settings.textSizeSubtitle': { ar: 'لتسهيل القراءة، يمكنك تكبير النصوص والأيقونات في كل صفحات التطبيق.', en: 'Make text and icons larger across the whole app for easier reading.' },
  'settings.textSize.normal': { ar: 'عادي', en: 'Normal' },
  'settings.textSize.large': { ar: 'كبير', en: 'Large' },
  'settings.textSize.xlarge': { ar: 'أكبر', en: 'Extra large' },
  'settings.language': { ar: 'اللغة', en: 'Language' },
  'settings.languageSubtitle': { ar: 'اختاري لغة الواجهة المفضّلة لديك.', en: 'Choose your preferred interface language.' },
  'settings.language.ar': { ar: 'العربية', en: 'Arabic' },
  'settings.language.en': { ar: 'English', en: 'English' },
  'settings.language.note': { ar: 'بعض الصفحات لا تزال بالعربية فقط أثناء استكمال الترجمة.', en: 'Some pages are still Arabic-only while translation is in progress.' },

  // DashboardPage (main guardian view — static labels only)
  'dashboard.kicker': { ar: 'مساحة العائلة', en: "Family space" },
  'dashboard.addChild': { ar: '＋ إضافة طفل', en: '＋ Add child' },
  'dashboard.shortcut.reports': { ar: 'التقارير', en: 'Reports' },
  'dashboard.shortcut.timeline': { ar: 'الخط الزمني', en: 'Timeline' },
  'dashboard.shortcut.goals': { ar: 'الأهداف', en: 'Goals' },
  'dashboard.shortcut.careTeam': { ar: 'فريق الرعاية', en: 'Care team' },
  'dashboard.shortcut.centers': { ar: 'مراكز مناسبة', en: 'Matching centers' },
  'dashboard.quickGlance': { ar: 'نظرة سريعة', en: 'At a glance' },
  'dashboard.viewDetails': { ar: 'عرض التفاصيل', en: 'View details' },
  'dashboard.services': { ar: 'الخدمات الحالية', en: 'Current services' },
  'dashboard.needs': { ar: 'الاحتياجات', en: 'Needs' },
  'dashboard.conditions': { ar: 'الحالات', en: 'Conditions' },
}

export function translate(key: string, lang: Language): string {
  const entry = translations[key]
  if (!entry) return key
  return entry[lang]
}
