-- name: world_series
SELECT o.year, i.indicator_id, i.energy_category, i.unit, o.value
FROM energy_observation o
JOIN geography g ON g.geo_id = o.geo_id
JOIN indicator i ON i.indicator_id = o.indicator_id
WHERE g.geography_type = 'world' AND o.release_id = 'owid-energy-2026-09-10'
ORDER BY o.year, i.indicator_id;

-- name: annual_coverage
SELECT o.year, g.geography_type, i.indicator_id, COUNT(*) AS slots,
       COUNT(o.value) AS observed, COUNT(*) - COUNT(o.value) AS missing,
       SUM(CASE WHEN o.value = 0 THEN 1 ELSE 0 END) AS observed_zero
FROM energy_observation o
JOIN geography g ON g.geo_id = o.geo_id
JOIN indicator i ON i.indicator_id = o.indicator_id
WHERE o.release_id = 'owid-energy-2026-09-10'
GROUP BY o.year, g.geography_type, i.indicator_id
ORDER BY o.year, g.geography_type, i.indicator_id;

-- name: countries_series
SELECT o.year, g.name, g.iso_code, i.indicator_id, i.energy_category, i.unit, o.value
FROM energy_observation o
JOIN geography g ON g.geo_id = o.geo_id
JOIN indicator i ON i.indicator_id = o.indicator_id
WHERE g.geography_type = 'iso_coded' AND g.iso_code IN ('CHN', 'DEU', 'IND', 'USA')
  AND o.release_id = 'owid-energy-2026-09-10'
ORDER BY g.name, o.year, i.indicator_id;
