-- 014: iodul din alimentele catalogului validat (generat de scripts/build_food_catalog.py --sql-iodine).
-- Sursa: USDA, FDA and ODS-NIH Database for the Iodine Content of Common Foods, Release 4.0 (2024),
-- µg / 100 g; maparea și motivele sunt în data/iodine_values.py. Alimentele nemapate rămân cu iod NULL.
begin;
update public.foods set iodine = 33.5 where food_key = 'milk_whole';  -- DB_ID 20, n=59
update public.foods set iodine = 35.8 where food_key = 'milk_semi';  -- DB_ID 21, n=59
update public.foods set iodine = 32.3 where food_key = 'yogurt_plain';  -- DB_ID 448, n=8
update public.foods set iodine = 51.2 where food_key = 'yogurt_greek';  -- DB_ID 361, n=6
update public.foods set iodine = 36.6 where food_key = 'cottage_cheese';  -- DB_ID 161, n=11
update public.foods set iodine = 66.0 where food_key = 'ricotta';  -- DB_ID 350, n=1
update public.foods set iodine = 45.9 where food_key = 'cheddar';  -- DB_ID 25, n=38
update public.foods set iodine = 51.0 where food_key = 'mozzarella';  -- DB_ID 191, n=30
update public.foods set iodine = 48.4 where food_key = 'feta';  -- DB_ID 450, n=8
update public.foods set iodine = 82.4 where food_key = 'parmesan';  -- DB_ID 349, n=9
update public.foods set iodine = 61.0 where food_key = 'egg_boiled';  -- DB_ID 34, n=35
update public.foods set iodine = 172.1 where food_key = 'cod';  -- DB_ID 186, n=28
update public.foods set iodine = 12.8 where food_key = 'salmon_farmed';  -- DB_ID 158, n=35
update public.foods set iodine = 12.8 where food_key = 'salmon_wild';  -- DB_ID 158, n=35
update public.foods set iodine = 3.2 where food_key = 'salmon_sashimi';  -- DB_ID 496, n=8
update public.foods set iodine = 8.7 where food_key = 'tuna_light_can';  -- DB_ID 166, n=15
update public.foods set iodine = 15.2 where food_key = 'shrimp';  -- DB_ID 132, n=39
update public.foods set iodine = 66.5 where food_key = 'clams';  -- DB_ID 392, n=4
update public.foods set iodine = 7.5 where food_key = 'beef_ground';  -- DB_ID 251, n=35
update public.foods set iodine = 4.7 where food_key = 'beef_lean';  -- DB_ID 260, n=34
update public.foods set iodine = 16.4 where food_key = 'beef_liver';  -- DB_ID 335, n=7
update public.foods set iodine = 0.4 where food_key = 'pork_tenderloin';  -- DB_ID 333, n=7
update public.foods set iodine = 1.2 where food_key = 'chicken_breast';  -- DB_ID 130, n=35
update public.foods set iodine = 0.9 where food_key = 'chicken_thigh';  -- DB_ID 163, n=35
update public.foods set iodine = 4.8 where food_key = 'turkey_breast';  -- DB_ID 30, n=35
update public.foods set iodine = 6.7 where food_key = 'spinach_raw';  -- DB_ID 206, n=27
update public.foods set iodine = 3.9 where food_key = 'spinach_cooked';  -- DB_ID 1, n=8
update public.foods set iodine = 0.5 where food_key = 'potato';  -- DB_ID 84, n=35
update public.foods set iodine = 0.1 where food_key = 'white_beans';  -- DB_ID 323, n=7
update public.foods set iodine = 0.0 where food_key = 'tofu';  -- DB_ID 458, n=1
update public.foods set iodine = 0.0 where food_key = 'almonds';  -- DB_ID 227, n=3
update public.foods set iodine = 0.4 where food_key = 'almond_milk';  -- DB_ID 210, n=9
update public.foods set iodine = 1.3 where food_key = 'soy_milk_fortified';  -- DB_ID 213, n=6
update public.foods set iodine = 0.2 where food_key = 'white_rice';  -- DB_ID 40, n=34
update public.foods set iodine = 0.0 where food_key = 'brown_rice';  -- DB_ID 200, n=28
update public.foods set iodine = 0.0 where food_key = 'quinoa';  -- DB_ID 223, n=3
update public.foods set iodine = 1.8 where food_key = 'white_bread';  -- DB_ID 46, n=15
update public.foods set iodine = 1.9 where food_key = 'wholewheat_bread';  -- DB_ID 48, n=21
update public.foods set iodine = 0.6 where food_key = 'rye_bread';  -- DB_ID 337, n=7
commit;
