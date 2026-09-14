import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { Center, CenterFilterOptions } from '../types'
import '../styles/centers.css'

type DeliveryMode = '' | 'in_person' | 'remote' | 'both'
type AgeGroup = '' | '0-5' | '6-12' | '13-18' | '18+'
type SortOption = 'recommended' | 'closest' | 'favorites' | 'name'

interface DirectoryFilters {
  q: string
  city: string
  specialty: string
  service: string
  ageGroup: AgeGroup
  deliveryMode: DeliveryMode
  favoritesOnly: boolean
}

const EMPTY_FILTERS: DirectoryFilters = {
  q: '',
  city: '',
  specialty: '',
  service: '',
  ageGroup: '',
  deliveryMode: '',
  favoritesOnly: false,
}

function deliveryLabels(center: Center) {
  const labels: string[] = []
  if (center.offers_in_person) labels.push('حضوري')
  if (center.offers_remote) labels.push('عن بعد')
  return labels
}

function ageLabel(center: Center) {
  if (center.min_age_years == null && center.max_age_years == null) return 'جميع الأعمار'
  if (center.min_age_years != null && center.max_age_years != null) {
    return `من ${center.min_age_years} إلى ${center.max_age_years} سنة`
  }
  if (center.min_age_years != null) return `من ${center.min_age_years} سنة فأكثر`
  return `حتى ${center.max_age_years} سنة`
}

// Straight-line (haversine) distance in km — approximate, not a driving distance.
function distanceKm(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function distanceValue(center: Center, userLocation: { lat: number; lon: number } | null) {
  if (!userLocation || center.latitude == null || center.longitude == null) return null
  return distanceKm(userLocation.lat, userLocation.lon, center.latitude, center.longitude)
}

function distanceLabel(center: Center, userLocation: { lat: number; lon: number } | null) {
  const km = distanceValue(center, userLocation)
  if (km == null) return null
  const rounded = km < 10 ? km.toFixed(1) : Math.round(km).toString()
  return `~${rounded} كم من موقعك (تقريبي، خط مستقيم)`
}

export default function CentersPage() {
  const [centers, setCenters] = useState<Center[]>([])
  const [options, setOptions] = useState<CenterFilterOptions>({ cities: [], specialties: [], services: [] })
  const [filters, setFilters] = useState<DirectoryFilters>(EMPTY_FILTERS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null)
  const [locating, setLocating] = useState(false)
  const [locationError, setLocationError] = useState('')
  const [savingFavoriteId, setSavingFavoriteId] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('recommended')

  useEffect(() => {
    apiClient.get<CenterFilterOptions>('/centers/filter-options')
      .then((response) => setOptions(response.data))
      .catch(() => setError('تعذر تحميل خيارات البحث. يمكنك المحاولة مرة أخرى.'))
  }, [])

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError('')
      apiClient.get<Center[]>('/centers', {
        params: {
          q: filters.q.trim() || undefined,
          city: filters.city || undefined,
          specialty: filters.specialty || undefined,
          service: filters.service || undefined,
          age_group: filters.ageGroup || undefined,
          delivery_mode: filters.deliveryMode || undefined,
          favorites_only: filters.favoritesOnly || undefined,
        },
      })
        .then((response) => {
          if (active) setCenters(response.data)
        })
        .catch(() => {
          if (active) setError('تعذر تحميل المراكز الآن. تحقق من الاتصال ثم حاول مجددًا.')
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, filters.q ? 300 : 0)

    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [filters])

  const hasFilters = useMemo(
    () => Object.entries(filters).some(([, value]) => Boolean(value)),
    [filters],
  )

  const sortedCenters = useMemo(() => {
    const list = [...centers]
    if (sortBy === 'closest') {
      return list.sort((a, b) => {
        const da = distanceValue(a, userLocation)
        const db = distanceValue(b, userLocation)
        if (da == null && db == null) return 0
        if (da == null) return 1
        if (db == null) return -1
        return da - db
      })
    }
    if (sortBy === 'favorites') {
      return list.sort((a, b) => Number(b.is_favorite) - Number(a.is_favorite) || a.name.localeCompare(b.name, 'ar'))
    }
    if (sortBy === 'name') {
      return list.sort((a, b) => a.name.localeCompare(b.name, 'ar'))
    }
    return list
  }, [centers, sortBy, userLocation])

  const updateFilter = <K extends keyof DirectoryFilters,>(key: K, value: DirectoryFilters[K]) => {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('المتصفح لا يدعم تحديد الموقع.')
      return
    }
    setLocating(true)
    setLocationError('')
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({ lat: position.coords.latitude, lon: position.coords.longitude })
        setLocating(false)
      },
      () => {
        setLocationError('تعذر الوصول إلى موقعك. يمكنك المتابعة بدون عرض المسافة.')
        setLocating(false)
      },
      { enableHighAccuracy: false, timeout: 10000 },
    )
  }

  const toggleFavorite = async (center: Center) => {
    if (savingFavoriteId) return
    setSavingFavoriteId(center.id)
    setError('')
    try {
      if (center.is_favorite) {
        await apiClient.delete(`/centers/${center.id}/favorite`)
      } else {
        await apiClient.put(`/centers/${center.id}/favorite`)
      }
      setCenters((current) => current
        .map((item) => item.id === center.id ? { ...item, is_favorite: !item.is_favorite } : item)
        .filter((item) => !(filters.favoritesOnly && item.id === center.id && center.is_favorite)))
    } catch {
      setError('تعذر تحديث المفضلة. حاول مرة أخرى.')
    } finally {
      setSavingFavoriteId('')
    }
  }

  return (
    <section className="centers-page">
      <div className="centers-hero">
        <div>
          <span className="soft-kicker">المراكز والخدمات</span>
          <h1>ابحث عن الخدمة المناسبة بسهولة</h1>
          <p>استعرض المراكز بحسب المدينة والتخصص وطريقة تقديم الخدمة، واحفظ ما ترغب في الرجوع إليه لاحقًا.</p>
        </div>
        <span className="centers-hero-mark" aria-hidden="true">⌖</span>
      </div>

      <div className="centers-location-bar">
        {userLocation ? (
          <span className="centers-location-active">✓ يتم عرض المسافة التقريبية من موقعك الحالي</span>
        ) : (
          <button type="button" className="btn btn-outline btn-small" onClick={useMyLocation} disabled={locating}>
            {locating ? 'جارٍ تحديد موقعك...' : '📍 عرض المسافة من موقعي'}
          </button>
        )}
        {locationError && <span className="centers-location-error">{locationError}</span>}
      </div>

      <form className="centers-filters" onSubmit={(event) => event.preventDefault()}>
        <label className="centers-search">
          <span>ابحث باسم المركز أو الخدمة</span>
          <div><span aria-hidden="true">⌕</span><input value={filters.q} onChange={(event) => updateFilter('q', event.target.value)} placeholder="مثال: تخاطب أو علاج وظيفي" /></div>
        </label>

        <div className="centers-filter-grid">
          <label><span>المدينة</span><select value={filters.city} onChange={(event) => updateFilter('city', event.target.value)}><option value="">كل المدن</option>{options.cities.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span>التخصص</span><select value={filters.specialty} onChange={(event) => updateFilter('specialty', event.target.value)}><option value="">كل التخصصات</option>{options.specialties.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span>الخدمة</span><select value={filters.service} onChange={(event) => updateFilter('service', event.target.value)}><option value="">كل الخدمات</option>{options.services.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label><span>الفئة العمرية</span><select value={filters.ageGroup} onChange={(event) => updateFilter('ageGroup', event.target.value as AgeGroup)}><option value="">كل الأعمار</option><option value="0-5">حتى 5 سنوات</option><option value="6-12">من 6 إلى 12 سنة</option><option value="13-18">من 13 إلى 18 سنة</option><option value="18+">18 سنة فأكثر</option></select></label>
          <label><span>طريقة تقديم الخدمة</span><select value={filters.deliveryMode} onChange={(event) => updateFilter('deliveryMode', event.target.value as DeliveryMode)}><option value="">كل الخيارات</option><option value="in_person">حضوري</option><option value="remote">عن بعد</option><option value="both">حضوري وعن بعد</option></select></label>
        </div>

        <div className="centers-filter-footer">
          <label className="favorites-filter"><input type="checkbox" checked={filters.favoritesOnly} onChange={(event) => updateFilter('favoritesOnly', event.target.checked)} /><span>عرض المفضلة فقط</span></label>
          {hasFilters && <button type="button" className="centers-clear" onClick={() => setFilters(EMPTY_FILTERS)}>مسح عوامل البحث</button>}
        </div>
      </form>

      {error && <div className="alert alert-error centers-alert" role="alert">{error}</div>}

      <div className="centers-results-head">
        <div><span className="soft-kicker">نتائج الدليل</span><h2>{loading ? 'جارٍ البحث...' : `${centers.length} مركز`}</h2></div>
        <label className="centers-sort">
          <span>الترتيب حسب</span>
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value as SortOption)}>
            <option value="recommended">مقترح (المفضلة أولاً)</option>
            <option value="closest">الأقرب أولاً</option>
            <option value="favorites">المفضلة أولاً</option>
            <option value="name">الاسم (أبجديًا)</option>
          </select>
        </label>
      </div>
      {sortBy === 'closest' && !userLocation && (
        <p className="centers-sort-hint">فعّلي «عرض المسافة من موقعي» أعلاه لترتيب المراكز حسب الأقرب فعليًا.</p>
      )}

      {loading ? (
        <div className="centers-loading" aria-live="polite"><div className="spinner" /><span>جاري تحميل المراكز...</span></div>
      ) : !centers.length ? (
        <div className="centers-empty">
          <span aria-hidden="true">⌕</span>
          <h2>{filters.favoritesOnly ? 'لا توجد مراكز محفوظة' : 'لم نجد مراكز مطابقة'}</h2>
          <p>{filters.favoritesOnly ? 'احفظ المراكز التي تهمك لتظهر هنا.' : 'جرّب تغيير المدينة أو الخدمة، أو استخدم كلمات بحث أقصر.'}</p>
          {hasFilters && <button className="btn btn-primary" type="button" onClick={() => setFilters(EMPTY_FILTERS)}>عرض كل المراكز</button>}
        </div>
      ) : (
        <div className="centers-grid">
          {sortedCenters.map((center) => (
            <article className="center-card" key={center.id}>
              <div className="center-card-head">
                <span className="center-card-icon" aria-hidden="true">⌂</span>
                <button
                  type="button"
                  className={`center-favorite ${center.is_favorite ? 'active' : ''}`}
                  onClick={() => void toggleFavorite(center)}
                  disabled={savingFavoriteId === center.id}
                  aria-pressed={center.is_favorite}
                  aria-label={center.is_favorite ? `إزالة ${center.name} من المفضلة` : `حفظ ${center.name} في المفضلة`}
                >{center.is_favorite ? '♥' : '♡'}</button>
              </div>
              <div className="center-card-location"><span aria-hidden="true">⌖</span>{center.city}{center.region ? `، ${center.region}` : ''}</div>
              <h2>{center.name}</h2>
              <p>{center.description}</p>
              <div className="center-card-tags">{center.specialties.slice(0, 3).map((item) => <span key={item}>{item}</span>)}</div>
              <div className="center-card-meta">
                <span>{deliveryLabels(center).join(' • ')}</span>
                <span>{ageLabel(center)}</span>
              </div>
              {distanceLabel(center, userLocation) && (
                <p className="center-card-distance">{distanceLabel(center, userLocation)}</p>
              )}
              <Link className="center-card-link" to={`/centers/${center.id}`}>عرض المركز <span aria-hidden="true">←</span></Link>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
