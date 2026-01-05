--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_users; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.admin_users (
    user_id bigint NOT NULL,
    username text,
    can_approve_payments boolean DEFAULT true,
    added_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admin_users OWNER TO telegram_user;

--
-- Name: channel_verification; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.channel_verification (
    user_id bigint NOT NULL,
    has_joined boolean DEFAULT false,
    verified_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.channel_verification OWNER TO telegram_user;

--
-- Name: destinations; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.destinations (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    title text,
    username text,
    rule_id text DEFAULT 'default'::text NOT NULL
);


ALTER TABLE public.destinations OWNER TO telegram_user;

--
-- Name: forwarding_delays; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.forwarding_delays (
    user_id bigint NOT NULL,
    rule_id text NOT NULL,
    delay_seconds integer DEFAULT 0
);


ALTER TABLE public.forwarding_delays OWNER TO telegram_user;

--
-- Name: forwarding_status; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.forwarding_status (
    user_id bigint NOT NULL,
    is_active boolean DEFAULT false,
    last_started timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.forwarding_status OWNER TO telegram_user;

--
-- Name: keyword_filters; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.keyword_filters (
    user_id bigint NOT NULL,
    rule_id text NOT NULL,
    type text NOT NULL,
    keywords text[] DEFAULT '{}'::text[],
    CONSTRAINT keyword_filters_type_check CHECK ((type = ANY (ARRAY['whitelist'::text, 'blacklist'::text])))
);


ALTER TABLE public.keyword_filters OWNER TO telegram_user;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    user_id bigint NOT NULL,
    message_text text,
    message_type character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.messages OWNER TO telegram_user;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: telegram_user
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO telegram_user;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: telegram_user
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    user_id bigint NOT NULL,
    plan_id text NOT NULL,
    amount real NOT NULL,
    payment_method text,
    transaction_id text,
    status text DEFAULT 'pending'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp without time zone,
    admin_id bigint,
    notes text,
    razorpay_order_id text,
    razorpay_payment_id text,
    razorpay_signature text,
    screenshot_message_id bigint
);


ALTER TABLE public.payments OWNER TO telegram_user;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: telegram_user
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO telegram_user;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: telegram_user
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: rules; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.rules (
    user_id bigint NOT NULL,
    rule_id text NOT NULL,
    name text,
    is_active boolean DEFAULT true,
    options jsonb DEFAULT '{}'::jsonb,
    manually_disabled boolean DEFAULT false
);


ALTER TABLE public.rules OWNER TO telegram_user;

--
-- Name: sources; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.sources (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    title text,
    rule_id text DEFAULT 'default'::text NOT NULL,
    username text
);


ALTER TABLE public.sources OWNER TO telegram_user;

--
-- Name: subscription_notifications; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.subscription_notifications (
    user_id bigint NOT NULL,
    last_expiry_notification timestamp without time zone,
    notified_for_plan text
);


ALTER TABLE public.subscription_notifications OWNER TO telegram_user;

--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.subscriptions (
    user_id bigint NOT NULL,
    plan text DEFAULT 'free'::text,
    expires_at timestamp without time zone,
    purchased_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notified_about_expiry boolean DEFAULT false,
    notified_about_expiry_soon boolean DEFAULT false
);


ALTER TABLE public.subscriptions OWNER TO telegram_user;

--
-- Name: user_activity; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.user_activity (
    user_id bigint NOT NULL,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    command_count integer DEFAULT 1,
    first_seen timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_activity OWNER TO telegram_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: telegram_user
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    phone text,
    session text,
    options jsonb DEFAULT '{}'::jsonb,
    current_rule text DEFAULT 'default'::text
);


ALTER TABLE public.users OWNER TO telegram_user;

--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Data for Name: admin_users; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.admin_users (user_id, username, can_approve_payments, added_at) FROM stdin;
1013148420	Admin	t	2025-09-11 09:00:13.218744
6331543504	Added by admin	f	2025-09-28 12:35:50.514703
\.


--
-- Data for Name: channel_verification; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.channel_verification (user_id, has_joined, verified_at) FROM stdin;
6331543504	t	2025-10-07 08:53:23.035818
8215282057	t	2025-10-07 09:02:49.827763
6532735248	t	2025-10-07 09:38:41.125937
742895166	t	2025-10-07 14:23:44.960586
7251995251	t	2025-10-07 14:41:05.509731
6222156706	t	2025-10-07 15:40:16.62787
2038045502	t	2025-10-07 17:16:44.284317
8282805291	t	2025-10-07 19:47:52.796898
7065067748	t	2025-10-07 21:12:22.522775
\.


--
-- Data for Name: destinations; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.destinations (user_id, chat_id, title, username, rule_id) FROM stdin;
1327566897	-1003157164503	Private Trades	\N	rule_1323614
7786809003	-5074879847	snap.alpha—OG algo	\N	rule_235523
7786809003	-5074879847	snap.alpha—OG algo	\N	rule_242224
1013148420	5762616457	LinkConvertTeraBot	LinkConvertTerabot	default
5023503076	-1003196185924	Prakrit course	\N	rule_2663138
7786809003	-5015734220	snap.alpha Raydium launchlab & bonkfun algo	\N	rule_243020
6159085054	-1003397240689	Crypto news	\N	rule_265926
7786809003	-5028530244	Test snap.coin	\N	rule_333451
6171495250	2015117555	ExtraPe Link Converter Bot (Official)	ExtraPeBot	rule_343254
8215282057	-1003001308069	Mukesh	\N	rule_1414695
6216309591	8346709989	Advance Auto Messege Forwarder Bot	advauto_messege_forwarder_bot	rule_414976
8126606818	8346709989	Advance Auto Messege Forwarder Bot	advauto_messege_forwarder_bot	rule_2754801
1013148420	5762616457	LinkConvertTeraBot	LinkConvertTerabot	rule_706016
8126606818	8366789774	Advance Auto Messege Forwarder Payment Bot	advance_forwarder_payment_bot	rule_2754801
8126606818	-4895122292	Dono	\N	rule_2754801
8126606818	-1003122579161	Dono	\N	rule_2754801
8012257232	-1003090449834	myxbot23	\N	rule_2817684
5479267800	-1002204094031	Valence Crypto 💎	\N	default
6292741991	-1003395609134	Santa Bnb	\N	rule_477180
6651813666	-1002335273300	𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗚𝗜𝗙𝗧 𝗛𝗨𝗕	\N	rule_1797231
7467184777	-1003023031978	Car 7777	\N	default
7467184777	-1003018383566	Car 0000	\N	default
7467184777	-1002940398044	Car For sale	\N	default
5821665830	-1003230661176	Sankalp UPSC हिन्दी माध्यम	\N	rule_2922360
5285734779	-1003395609134	Santa Bnb	\N	rule_477746
7452823412	-1003095011138	>𝕮𝖗𝖞𝖕𝖙𝖔 𝕭𝖔𝖝𝖃<	\N	rule_680791
5479267800	-1002204094031	Valence Crypto 💎	\N	rule_528858
6640526724	-1002204094031	Valence Crypto 💎	\N	rule_628749
6059788941	-1002262614815	Official anjali	\N	rule_1974928
1916333182	-1002204094031	Valence Crypto 💎	\N	rule_629316
6490654709	-1002796076356	Market Updates | Think Forge	\N	rule_3000381
1013148420	8324819345	tg forwarder	tg2forwarder_bot	rule_706225
1013148420	-1001814838516	Rosey Viral Links😍💋🥵	\N	rule_139720
809117482	-1003009613966	KD TEST	\N	default
1931035542	-1002204094031	Valence Crypto 💎	\N	rule_629578
7903348966	-1003109137305	🔥 XCIRCLE ⚡️	\N	rule_3027426
5081757613	803105693	Bittu	\N	default
6532735248	-1002335273300	𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗚𝗜𝗙𝗧 𝗛𝗨𝗕	\N	rule_1432510
5803322217	-1001610688795	Grow Club Institution Chat	\N	rule_526652
6876318627	-1003452258179	NYX Trading	\N	rule_666944
8282805291	6310459229	D s	\N	rule_1453303
7337643152	-1003095011138	>𝕮𝖗𝖞𝖕𝖙𝖔 𝕭𝖔𝖝𝖃<	\N	rule_779226
7786809003	-1003640260396	snap.alpha—OG algo v.2.0	\N	rule_857969
7903348966	-1003109137305	🔥 XCIRCLE ⚡️	\N	rule_3046200
5081757613	2015117555	ExtraPe Link Converter Bot (Official)	ExtraPeBot	rule_253652
742895166	-1003034132427	EGurukul	\N	rule_1435917
1013148420	-1003186090773	Super Shop deals	\N	rule_309529
1013148420	2015117555	ExtraPe Link Converter Bot (Official)	ExtraPeBot	rule_309764
8083890417	-1001417241897	Free 1k subscriber in 1 month Youtube	\N	rule_452475
8083890417	-1001758792916	Free 1k you tube subscriber	\N	rule_452475
6087538623	-1003186426214	𝗝𝗔𝗟𝗪𝗔 𝗣𝗥𝗜𝗩𝗔𝗧𝗘 𝗚𝗜𝗙𝗧 𝗖𝗢𝗗𝗘𝗦	\N	rule_1894044
8064447179	-1001820393936	YOUTUBE FREE SUBSCRIBER 1K SUBSCRIBER 4K WACHTIME	\N	rule_475987
8064447179	-1001474081644	INDIAN SUB 4SUB YOUTUBER	\N	rule_475987
8064447179	-1002357057872	Subscribe Exchange Free 2024	\N	rule_475987
8064447179	-1001217282906	YOUTUBE SUB4SUB GROUP	\N	rule_475987
8127040286	-1001915606317	WSOTP	\N	rule_2161171
8127040286	-1002055246264	Dubai News 365 / أخبار دبي / দুবাই সংবাদ / Дубай Новости / Noticias de Dubái / 杜拜新聞	\N	rule_2161171
906648890	906648890	Bikash	\N	rule_571886
8224373261	-1003122083289	Anime Database	\N	rule_2196849
7162132327	-1003015178011	ESHAN VIP🥶	\N	rule_662429
7611856186	-1003128707144	Test2	\N	rule_1571852
7433900109	-1003101242093	—͞ Mᴇʜᴅɪ ᴘʀɪᴠꫝᴛᴇ	\N	rule_3139397
8258901462	-1003043675141	QUOTEX 1 ON 1	\N	rule_2210712
6532735248	-1002335273300	𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗚𝗜𝗙𝗧 𝗛𝗨𝗕	\N	rule_1597589
6654944138	7533758507	CALLBOMBER NET	callbombernet_bot	rule_1602200
8127965483	-1002993404667	HM VIP Trading Gold📈💶	\N	rule_3147250
8370995918	-1002198121879	Indian bank accounta印度车队交流	\N	rule_3186888
6477484866	-1003156647910	Nafea capital ( توصيات)	\N	rule_2294630
6434063803	-1001159785638	Super Tips	\N	rule_920978
6434063803	-1001348150491	Super Tips	\N	rule_920978
7693672756	-1003043675141	QUOTEX 1 ON 1	\N	rule_3251577
5848770400	-1003157164503	Private Trades	\N	rule_3252653
7337643152	7066339174	🦅𝑸𝑨𝒁𝑨𝑿𝑳𝑰🦅	\N	default
7669122337	-1002696183477	IS KAASHI GROUP 📊 📈	\N	rule_2490482
7404167930	6317295439	EarnKaro Converter 9	ekconverter9bot	rule_1121253
5773544941	-1002790611573	GOOD SLOTS CODES HERE 🪐	\N	rule_1173686
5773544941	6901156650	MR GUNTISS	\N	rule_1173686
6331543504	-1002926832954	Testchannel3	\N	rule_3430271
6222156706	-1003199310757	XAUUSD	\N	rule_1202605
7693090424	-1002981934268	Y	\N	rule_1787862
6799961892	7472566378	avinash	\N	rule_1788421
6799961892	-1001818579939	𝐑𝐊 𝐀𝐑𝐌𝐘 / 𝐃𝐌𝐖𝐈𝐍 📈	\N	rule_1788421
6799961892	-1003171071528	𝐒𝐈𝐆𝐌𝐀 𝐕𝐈𝐏 𝐒𝐇𝐎𝐑𝐓𝐒	\N	rule_1788421
7209556360	-1003186792595	All in one 18 +	\N	rule_3452808
6636522096	-5076587170	test1	\N	rule_3487339
6830041427	-1002437675322	All yono games	\N	rule_3506946
7154763189	-1002335273300	𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗚𝗜𝗙𝗧 𝗛𝗨𝗕	\N	rule_1529434
7251995251	-1003160854831	Doc Tutorial	\N	rule_2566221
7786809003	-5093383928	Snap.alpha—stream scalping algo	\N	rule_243133
7786809003	-5062381331	snap.alpha— four.meme algo (beta)	\N	rule_243252
7796576246	-1003184075345	DreamCAST TV (Events & Fixtures)	\N	rule_3623961
8069225688	-1002191607346	💥 GAME CHANGER 💥	\N	rule_3675538
7962843287	-1002992561424	Hridayam Lotters Official (2.0)	\N	rule_358910
8360443949	-1002148375787	File store channel	\N	rule_299453
723189008	-1003208312501	Trading	\N	rule_3733604
5843862754	-1002204094031	Valence Crypto 💎	\N	rule_451484
7488003312	-1002341140504	𝐆𝐈𝐅𝐓 𝐂𝐎𝐃𝐄 𝐋𝐎𝐓𝐓𝐄𝐑𝐒	\N	default
8063683486	-1001689955991	𝗣𝗿𝗶𝗻𝗰𝗲 𝗦𝘂𝗿𝗲𝗦𝗵𝗼𝘁 🚀	\N	rule_521570
5803322217	-1002130021294	PUBLIC TRENDING	\N	rule_526652
7488003312	-1002341140504	𝐆𝐈𝐅𝐓 𝐂𝐎𝐃𝐄 𝐋𝐎𝐓𝐓𝐄𝐑𝐒	\N	rule_3782901
7098716789	7098716789	Aidarkhan	\N	rule_591291
5920013494	-1002204094031	Valence Crypto 💎	\N	rule_630475
6027932766	-1002117146781	𝐋𝐀𝐓𝐄𝐒𝐓 𝐌𝐎𝐕𝐈𝐄	\N	rule_66773
8280548411	7170069511	Martyn Beasley	\N	rule_110584
5747969128	-1002204094031	Valence Crypto 💎	\N	rule_631076
5457458340	-1002204094031	Valence Crypto 💎	\N	rule_631366
6588828344	-1003299509460	personal trades	\N	rule_134856
2012655294	-1002848456311	Premium Option Trading call	\N	rule_195606
1992060940	-1003186362121	Mv DATABASE	\N	rule_1677556
8276262057	-1003487138259	یدک گ 2025 1	\N	rule_1682557
7319777571	-1003293381119	Share market call	\N	default
5663097688	-1001967691908	Madras Trader T10	\N	rule_209096
7034015842	-1003437961809	91Club 100-200-500rs	\N	rule_858214
5445448223	-5075528205	Data XU JanB	\N	rule_240672
6305231297	-1002805436353	Personal apps	\N	rule_303725
7714089439	-1002246692175	Super Tips	\N	rule_860315
742895166	-1003434240331	DAMS BACK 2 BASICS 2025	\N	rule_502088
6779399346	-1002246692175	Super Tips	\N	rule_550914
7430101095	-1003280822282	The Halal Trader	\N	rule_672142
5964390462	-1003225120720	Halal World	\N	rule_706573
7752022043	-1002726520891	𝗔𝗻𝗶𝗺𝗮𝘁𝗲𝗱 𝗣𝗼𝗿𝗻 🫦	\N	rule_722960
7669122337	-1002696183477	IS KAASHI GROUP 📊 📈	\N	rule_2488327
6366929184	-1002682886989	perfect deals😊	\N	default
7065067748	-1002607579978	𝑴𝒐𝒏𝒌𝒆𝒚 𝒄𝒓𝒚𝒑𝒕𝒐 𝒃𝒐𝒙 🎧	\N	rule_919674
8260737582	-1002643216480	𝗔𝗖𝗧𝗥𝗘𝗦𝗦 𝗨𝗡𝗦𝗘𝗘𝗡 🥵 𝗥𝗘𝗗	\N	rule_1068508
6551218990	8346709989	Advance Auto Messege Forwarder Bot	advauto_messege_forwarder_bot	rule_1235124
7636116711	-1003328833878	91 Club 30rs	\N	rule_1491584
8281707866	-1003238661637	The Legend is back !	\N	rule_1557538
6818938551	777000	Telegram	\N	rule_425990
6013957379	-5082360740	TestRichDev	\N	rule_500083
1444313827	-1003223983848	METRO 45,60	\N	rule_511409
530131604	-5081370219	Lybozping	\N	default
8494703426	-1003407187039	BOT AO VIVO	\N	rule_831899
625596166	-1001275759474	best movies49	\N	rule_211950
1019557777	-1003416353887	Cinema nabbbb	\N	rule_212814
7047677983	-1003389088363	Manish auto 2	\N	rule_5484
6421644491	-1002340652523	𝘼𝙇𝙁𝘼 𝙀𝘼𝙍𝙉𝙄𝙉𝙂 𝙏𝙍𝙄𝙆𝙎	\N	rule_225354
7866745942	8166741952	P77 | Official Bot	P77Game_bot	rule_1813541
6271999767	-1003140434009	💵𝕏𝔸𝕌𝕌𝕊𝔻💶𝕂𝕀𝕃𝕃𝔸ℤ💷 𝕍𝟙	\N	rule_1891516
1992060940	-1003268395712	Telugu Anime	\N	rule_1895892
1992060940	-1003249963078	Mv DATABASE 2	\N	rule_302840
8562904531	-1003346211677	Prime Hot VIP ..	\N	rule_1336
8357880060	-1002204094031	Valence Crypto 💎	\N	rule_443947
5907554483	-1002204094031	Valence Crypto 💎	\N	rule_452727
5794338335	-1002204094031	Valence Crypto 💎	\N	rule_631776
487621983	7825253526	Forextrade	Forexexecutionbot	rule_687069
6331543504	8324819345	tg forwarder	tg2forwarder_bot	rule_1334118
7238808048	8236128760	@LinkConvertTerabot	LinkConvertTera3bot	rule_847843
7238808048	-1003643151351	Instagrami Duniyaa🌝❤️💀	\N	rule_847866
7786809003	-1003624219861	snap.alpha—pump.fun algo	\N	rule_242682
8012129273	-1003263659514	S 1	\N	rule_1036761
8431307336	-1001241628112	O'zbekiston 24 Tezkor	\N	rule_230046
7301764474	-1002542227207	Ꮆʜᴏꜱᴛ ᴇᴀʀɴɪɴɢ (Ꭷꜰꜰɪᴄɪᴀʟ) 💸	\N	rule_328716
7301764474	-1003170848757	𝙐𝙟𝙟𝙬𝙖𝙡 𝙏𝙞𝙥𝙨	\N	rule_330535
636735577	-1003434992897	Flutter Exercise	\N	rule_629274
7635975214	-5057638288	𝗚𝗮𝗺𝗮 567 ~ 𝗩𝗜𝗣 𝗠𝗔𝗧𝗞𝗔	\N	rule_821313
7844185193	-1003269665677	𝓐𝓰 𝓽є𝓬𝓱 σтρ gяσυρ	\N	rule_120843
8594095910	-1003330680565	Chinoz kanali	\N	rule_36683
1738839153	-1003404926954	Signal channel Mitja	\N	rule_307630
8566633996	-1003395568625	NITISH FX VIP GROUP	\N	rule_189993
535085855	-1001755844887	Fx Trading Pro Signals	\N	rule_332600
6082027138	6317295439	EarnKaro Converter 9	ekconverter9bot	rule_333452
8357312111	-1002410696606	𝙍𝙖𝙟𝙖 𝙂𝙖𝙢𝙚𝙨 𝙊𝙛𝙛𝙞𝙘𝙞𝙖𝙡 📈	\N	rule_6238
8288097205	-1002148375787	File store channel	\N	rule_42011
8566633996	-1003395568625	NITISH FX VIP GROUP	\N	rule_59028
5451735544	-5038203135	PenguinPay Coustomer Support Group	\N	rule_265425
6521860950	-1002806162097	CRYPTO INGPO	\N	rule_314698
5090523346	-1003213753026	Breach	\N	rule_403738
8213596906	-1002204094031	Valence Crypto 💎	\N	rule_444635
6617326165	-1003614473250	TMW Dump	\N	rule_299365
7560420076	-1001985222102	💢 Telegram Group Channel Links 💢	\N	rule_108595
6942557751	-1002148375787	File store channel	\N	rule_128212
7827652929	-1002204094031	Valence Crypto 💎	\N	rule_525672
7441972956	-1002204094031	Valence Crypto 💎	\N	rule_526198
7300111554	2015117555	ExtraPe Link Converter Bot (Official)	ExtraPeBot	rule_216260
7835273890	-1003610119029	Jalwa.game official🎯🎮🎰	\N	rule_214257
5803322217	-1002238399099	Valence Launch Project✈️	\N	rule_526652
7829152048	-1002204094031	Valence Crypto 💎	\N	rule_527237
7428775931	-1002204094031	Valence Crypto 💎	\N	rule_527822
7897782049	-789181897	KG LINE MC1146577 / Emerge	\N	rule_584660
8431059443	2015117555	ExtraPe Link Converter Bot (Official)	ExtraPeBot	rule_782064
5227137974	-1002033148975	Eran With Hardik	\N	rule_851637
6396777448	-4995264103	Hul	\N	default
8329946072	-1002995868798	Farru Looters (Official)	\N	rule_1249508
6031182200	-5296695575	The Chosen One and Sully	\N	rule_1292813
2061093227	-1003548783905	My bridge signal	\N	rule_1306930
7500700453	-1003330680565	Chinoz kanali	\N	default
7500700453	-1003330680565	Chinoz kanali	\N	rule_1384049
8000547764	5650405556	Tremaini	\N	rule_1418446
7555800019	-1003551404273	TEAM AZXXY	\N	rule_1809177
7555800019	-1001907316509	DAMAN HUB VIP	\N	rule_1809177
7555800019	-1001938388985	𝟗𝟏 𝐂𝐋𝐔𝐁 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 𝟎.𝟒	\N	rule_1809177
7555800019	-1002147256526	Jalwa Game Official Hub	\N	rule_1809177
7555800019	-1001638898352	DAMAN VIP 24/7 𝐆𝐑𝐎𝐔𝐏	\N	rule_1809177
7555800019	-1001320527616	😍BIG DADY 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍𝐒💥	\N	rule_1809177
7555800019	-1002243169588	Tashan Win Game	\N	rule_1809177
7555800019	-1002280997888	TASHAN WIN GUROP 24*7	\N	rule_1809177
7555800019	-1001762380124	Sikkim And Tashan Win Prediction	\N	rule_1809177
7555800019	-1002202173424	𝐃𝐀𝐌𝐀𝐍 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝐂𝐋𝐔𝐁 2.0	\N	rule_1809177
7555800019	-1002062483235	𝐃𝐀𝐌𝐀𝐍 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 𝟎.𝟔	\N	rule_1809177
7555800019	-1002220625150	JALWA TRADE	\N	rule_1809177
7555800019	-1002251754513	TASHAN WIN FREE PRIDICTION🔥🔥🔥🔥	\N	rule_1809177
7555800019	-1002231993939	乂ᴳᵒᵈ乂𝐋𝐞𝐯𝐞𝐥 24×7ᏀᎡᎧᏌᏢ❗❗	\N	rule_1809177
7555800019	-1002180218102	TASHAN - WIN / >> NEVER LOSS	\N	rule_1809177
7555800019	-1001797816647	DAMAN FREE PRIDICTION🔥	\N	rule_1809177
7555800019	-1002151893004	PROFIT WITH JIGAR	\N	rule_1809177
7555800019	-1001980155914	DAMAN HUB VIP	\N	rule_1809177
7555800019	-1002261090778	AGENT gc ⇨Ꮙｴ𝙋☔️	\N	rule_1809177
7555800019	-1002406929186	𝐕𝐈𝐏 𝐒𝐔𝐑𝐄 𝐒𝐇𝐎𝐓 𝐇𝐔𝐁	\N	rule_1809177
7555800019	-1001812614530	TEAM RR OFFICIAL 😈	\N	rule_1809177
7555800019	-1001898950278	🔥BIG DADY 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍𝐒 🔥	\N	rule_1809177
7555800019	-1002020682061	𝐃𝐀𝐌𝐀𝐍 𝐕.𝐈.𝐏. 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍	\N	rule_1809177
7555800019	-1002174621002	𝗗𝗠𝗪𝗜𝗡 𝗩𝗜𝗣 𝗛𝗨𝗕	\N	rule_1809177
7555800019	-1002319272047	𝐁ɪʟʟɪᴏɴᴀɪʀᴇ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 💯	\N	rule_1809177
7555800019	-1001962549546	6 club 𝐋𝐎𝐓𝐓𝐄𝐑𝐘 𝐆𝐑𝐎𝐔𝐏	\N	rule_1809177
7555800019	-1002509813648	RICH X SIGMA OFFICIAL GROUP	\N	rule_1809177
7555800019	-1002491682368	PREDICTION FREE HACK	\N	rule_1809177
7555800019	-1002317296322	𝐃𝐌𝐖𝐈𝐍 𝐒𝐔𝐌𝐈𝐓 𝐁𝐇𝐀𝐈	\N	rule_1809177
7555800019	-1002711484414	亗 ꪜɪʀᴀᴛ ࿐𝐋𝐞𝐯𝐞𝐥 24×7ᏀᎡᎧᏌᏢ	\N	rule_1809177
7555800019	-1001865837735	BIG DADDY PREDICTION 1 MINUTE NONSTOP	\N	rule_1809177
7555800019	-1002359542722	SIKKIM GAME OFFICIAL GROUP	\N	rule_1809177
7555800019	-1002320027019	SIKKIM GAME PREDICTION	\N	rule_1809177
7555800019	-1002092161664	DAMAN BY SHEIKH	\N	rule_1809177
7555800019	-1002166991097	𝐃𝐀𝐌𝐀𝐍 𝗢𝐅𝐅𝐈𝐂𝐀𝐋 𝟎𝟑	\N	rule_1809177
7555800019	-1002382972181	Bdg win prediction	\N	rule_1809177
7555800019	-1002345900505	Jalwa Game 🤑 🇮🇳	\N	rule_1809177
7555800019	-1002663416546	JALWA GAME CLUB ❤️	\N	rule_1809177
7555800019	-1002232636606	𝗕𝗢𝗨𝗡𝗧𝗬 [ 𝗩𝗜𝗣 ] 𝗛𝗨𝗕	\N	rule_1809177
7555800019	-1002592566609	DAMAN VIP HUB	\N	rule_1809177
7555800019	-1002222950998	JALWA GAME NON STOP PREDICTION	\N	rule_1809177
5689065087	-1002443619013	Gift Code With Lala ☠️	\N	rule_536552
7555800019	-1002153809828	KWG PREDICTION VIP GROUP ️	\N	rule_1809177
7555800019	-1001997397426	𝐃𝐀𝐌𝐀𝐍 𝐋𝐀𝐓𝐄 𝐍𝐈𝐆𝐇𝐓 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋	\N	rule_1809177
7555800019	-1002331589835	DAMAN VIP GROUP	\N	rule_1809177
7555800019	-1002199633130	BDG GAME PREDICTION	\N	rule_1809177
7555800019	-1002739911563	👑 KHALNYAK KA GROUP	\N	rule_1809177
7555800019	-1002557082104	VIP WINNING HUN	\N	rule_1809177
7555800019	-1002043819296	𝐁𝐃𝐆 𝐆𝐀𝐌𝐄 𝐕𝐈𝐏 ❷❹×➐ 𝐆𝐑𝐎𝐔𝐏 👑	\N	rule_1809177
7555800019	-1002690895376	—͟͞͞𝗧𝗔𝗦𝗛𝗔𝗡 𝗪𝗜𝗡 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗛𝗨𝗕	\N	rule_1809177
7555800019	-1002509813648	RICH X SIGMA OFFICIAL GROUP	\N	rule_1807764
7555800019	-1002663416546	JALWA GAME CLUB ❤️	\N	rule_1807764
7555800019	-1002382972181	Bdg win prediction	\N	rule_1807764
7555800019	-1001963128845	𝐓𝐀𝐒𝐇𝐀𝐍 𝐖𝐈𝐍 𝐄𝐗𝐏𝐄𝐑𝐓	\N	rule_1807764
7555800019	-1002166991097	𝐃𝐀𝐌𝐀𝐍 𝗢𝐅𝐅𝐈𝐂𝐀𝐋 𝟎𝟑	\N	rule_1807764
7555800019	-1002431812289	Tashan	\N	rule_1807764
7555800019	-1001582599957	SIKKIM GAMES FREE PRIDICTION 🔥🔥🔥🔥🔥	\N	rule_1807764
7555800019	-1001638898352	DAMAN VIP 24/7 𝐆𝐑𝐎𝐔𝐏	\N	rule_1807764
7555800019	-1001320527616	😍BIG DADY 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍𝐒💥	\N	rule_1807764
7555800019	-1002231993939	乂ᴳᵒᵈ乂𝐋𝐞𝐯𝐞𝐥 24×7ᏀᎡᎧᏌᏢ❗❗	\N	rule_1807764
7555800019	-1001762380124	Sikkim And Tashan Win Prediction	\N	rule_1807764
7555800019	-1002062483235	𝐃𝐀𝐌𝐀𝐍 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 𝟎.𝟔	\N	rule_1807764
7555800019	-1002592566609	DAMAN VIP HUB	\N	rule_1807764
7555800019	-1002624447173	BDG GAME DISCUSSION	\N	rule_1807764
7555800019	-1002319272047	𝐁ɪʟʟɪᴏɴᴀɪʀᴇ 𝐏ʀᴇᴅɪᴄᴛɪᴏɴ 💯	\N	rule_1807764
7555800019	-1002280997888	TASHAN WIN GUROP 24*7	\N	rule_1807764
7555800019	-1001797816647	DAMAN FREE PRIDICTION🔥	\N	rule_1807764
7555800019	-1001898950278	🔥BIG DADY 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍𝐒 🔥	\N	rule_1807764
7555800019	-1001812614530	TEAM RR OFFICIAL 😈	\N	rule_1807764
7555800019	-1002640027133	𝗧𝗥𝗔𝗗𝗘𝗥 𝗣𝗨𝗥𝗔𝗕 𝗚𝗥𝗨𝗣	\N	rule_1807764
7555800019	-1002180218102	TASHAN - WIN / >> NEVER LOSS	\N	rule_1807764
7555800019	-1002174621002	𝗗𝗠𝗪𝗜𝗡 𝗩𝗜𝗣 𝗛𝗨𝗕	\N	rule_1807764
7555800019	-1002153809828	KWG PREDICTION VIP GROUP ️	\N	rule_1807764
7555800019	-1002406929186	𝐕𝐈𝐏 𝐒𝐔𝐑𝐄 𝐒𝐇𝐎𝐓 𝐇𝐔𝐁	\N	rule_1807764
7555800019	-1002128211857	𝙂𝙤𝙖 𝙂𝙖𝙢𝙚𝙨 𝙑𝙄𝙋🔥	\N	rule_1807764
7555800019	-1002092161664	DAMAN BY SHEIKH	\N	rule_1807764
7555800019	-1001980155914	DAMAN HUB VIP	\N	rule_1807764
7555800019	-1001907316509	DAMAN HUB VIP	\N	rule_1807764
7555800019	-1002020682061	𝐃𝐀𝐌𝐀𝐍 𝐕.𝐈.𝐏. 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍	\N	rule_1807764
7555800019	-1002220625150	JALWA TRADE	\N	rule_1807764
7555800019	-1002690895376	—͟͞͞𝗧𝗔𝗦𝗛𝗔𝗡 𝗪𝗜𝗡 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗛𝗨𝗕	\N	rule_1807764
7555800019	-1002202173424	𝐃𝐀𝐌𝐀𝐍 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝐂𝐋𝐔𝐁 2.0	\N	rule_1807764
7555800019	-1002243169588	Tashan Win Game	\N	rule_1807764
7555800019	-1001997397426	𝐃𝐀𝐌𝐀𝐍 𝐋𝐀𝐓𝐄 𝐍𝐈𝐆𝐇𝐓 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋	\N	rule_1807764
7555800019	-1002222950998	JALWA GAME NON STOP PREDICTION	\N	rule_1807764
7555800019	-1002261090778	AGENT gc ⇨Ꮙｴ𝙋☔️	\N	rule_1807764
7555800019	-1002147256526	Jalwa Game Official Hub	\N	rule_1807764
7555800019	-1001938388985	𝟗𝟏 𝐂𝐋𝐔𝐁 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 𝟎.𝟒	\N	rule_1807764
7555800019	-1002223899842	JALWA HUB VIP	\N	rule_1807764
7555800019	-1002641207295	51 GAME DAILY PROFITS	\N	rule_1807764
7555800019	-1002199633130	BDG GAME PREDICTION	\N	rule_1807764
7555800019	-1002251754513	TASHAN WIN FREE PRIDICTION🔥🔥🔥🔥	\N	rule_1807764
7555800019	-1001865837735	BIG DADDY PREDICTION 1 MINUTE NONSTOP	\N	rule_1807764
7555800019	-1001962549546	6 club 𝐋𝐎𝐓𝐓𝐄𝐑𝐘 𝐆𝐑𝐎𝐔𝐏	\N	rule_1807764
7555800019	-1002491682368	PREDICTION FREE HACK	\N	rule_1807764
7555800019	-1002345900505	Jalwa Game 🤑 🇮🇳	\N	rule_1807764
7555800019	-1002317296322	𝐃𝐌𝐖𝐈𝐍 𝐒𝐔𝐌𝐈𝐓 𝐁𝐇𝐀𝐈	\N	rule_1807764
7555800019	-1002043710002	𝘿𝙖𝙢𝙖𝙣 𝙂𝙖𝙢𝙚 - 𝗦𝗨𝗣𝗘𝗥 모 🎀	\N	rule_1807764
7555800019	-1002232636606	𝗕𝗢𝗨𝗡𝗧𝗬 [ 𝗩𝗜𝗣 ] 𝗛𝗨𝗕	\N	rule_1807764
7555800019	-1003288148007	𝗗𝗔𝗠𝗔𝗡 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡	\N	rule_1807764
6848720005	7247805209	DW2DW_LinkConverterBot	DW2DW_LinkConverterBot	rule_1448114
6848720005	-1003606043662	Bhai Bhen Ki Videos😻❤️	\N	rule_1448198
6848720005	8239533197	@LinkConvertTerabot	LinkConvertTera2bot	rule_1449885
6848720005	-1003643151351	Instagrami Duniyaa🌝❤️💀	\N	rule_1449943
6848720005	8382618961	@LinkConvertTerabot	LinkConvertTeraAbot	rule_1450102
6848720005	-1003130842324	Viral wala Bhaiya ji😭💋	\N	rule_1450181
6848720005	8236128760	@LinkConvertTerabot	LinkConvertTera3bot	rule_1450242
7353874683	-1003483699945	Movie house 😏	\N	rule_842862
6848720005	-1003538065930	InstaGram All Links😻	\N	rule_1450317
8252877204	-1001615165126	Selling USDT for Indian rupees(INR)	\N	rule_1458612
7885730692	-1002250280428	Wealth Genius News And Updates📈	\N	rule_1521283
5662756526	-1003415304145	Garant Savdo | #UZG	\N	rule_1560286
6331543504	-1002926832954	Testchannel3	\N	rule_1334118
7619204326	-1003269436111	🔥100x Zone⚡️	\N	rule_1688614
8188198606	-1002399922190	Video viral forward	\N	rule_1691815
8533537899	-1003629179518	ZAP PAY	\N	rule_1702735
7187275939	-1003456621553	Rzk Otp	\N	default
5604698232	-1002252290239	👑 PATEL 👑	\N	default
6848720005	7247805209	DW2DW_LinkConverterBot	DW2DW_LinkConverterBot	rule_38028
6848720005	-1003679196172	INSTAGRAM LINKS ALL❤️😚	\N	rule_38098
6848720005	7247805209	DW2DW_LinkConverterBot	DW2DW_LinkConverterBot	rule_38176
6848720005	-1003320784392	INSTA DUNIYAAA🍆❤️	\N	rule_38211
5112004413	6683320109	EarnKaro Converter 11	ekconverter11bot	rule_40037
\.


--
-- Data for Name: forwarding_delays; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.forwarding_delays (user_id, rule_id, delay_seconds) FROM stdin;
6331543504	rule_832187	2
6331543504	rule_1340980	2
1013148420	rule_706225	0
1013148420	rule_706016	1
6490654709	rule_2563068	0
1992060940	rule_3434397	15
8281707866	rule_3621573	60
1992060940	rule_3601027	25
1992060940	rule_3671427	30
1992060940	rule_3742340	60
1992060940	rule_1895892	60
7246249229	rule_426101	0
1992060940	rule_1677556	30
7555800019	rule_1809177	0
5285734779	rule_477746	30
7098716789	default	0
7897782049	rule_584660	0
1992060940	rule_302840	60
\.


--
-- Data for Name: forwarding_status; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.forwarding_status (user_id, is_active, last_started) FROM stdin;
8282805291	t	2025-10-07 19:48:03.390585
8083890417	t	2025-09-26 00:24:25.920455
2110346594	t	2025-09-26 05:37:50.946799
8064447179	f	2025-09-26 07:13:53.373433
7159663819	t	2025-09-27 00:18:02.665388
7404167930	t	2025-10-12 21:10:23.727135
7047677983	t	2025-12-11 23:37:44.803847
6651813666	f	2025-10-15 20:55:34.478119
7946534196	t	2025-10-10 07:52:37.794978
7430101095	t	2025-11-12 02:25:00.806368
6594077403	t	2025-09-30 21:34:02.164125
8566633996	t	2025-12-15 08:13:52.8376
8215282057	t	2025-10-07 09:03:00.830992
6434063803	t	2025-10-01 13:11:14.085614
1026086849	f	2025-11-25 12:56:51.475994
6222156706	t	2025-10-13 12:45:56.746563
1020100092	t	2025-10-03 10:30:07.20634
6521860950	t	2025-12-15 15:44:27.564767
2012655294	f	2025-11-06 19:24:28.446803
8224373261	t	2025-10-17 22:11:19.660818
5907554483	t	2025-12-17 03:51:29.215303
6806787718	t	2025-10-08 12:26:06.032598
8140482478	t	2025-10-30 16:41:59.597164
7337643152	t	2025-12-20 22:38:11.612089
7903348966	t	2025-10-26 12:10:55.145179
6654944138	t	2025-10-09 13:09:54.216343
5773544941	f	2025-10-04 15:13:27.399391
8281707866	f	2025-11-22 11:07:54.733164
1327566897	t	2025-10-06 11:22:21.679137
5023503076	t	2025-10-21 21:39:36.992574
7162132327	f	2025-12-12 01:31:07.280447
8000635184	t	2025-10-22 10:20:44.776704
762265169	f	2025-10-17 14:19:51.053468
8127965483	f	2025-10-30 19:45:07.20293
7611856186	t	2025-10-10 17:59:58.200089
7635975214	f	2025-12-06 11:55:37.792321
7065067748	f	2025-11-20 22:19:00.71228
5989213998	t	2025-10-12 17:57:22.03944
8126606818	t	2025-10-22 23:36:38.823838
8012257232	t	2025-10-23 17:02:20.51595
530131604	t	2025-12-03 16:04:39.184001
7154763189	f	2025-10-13 20:38:16.225472
7636116711	t	2025-11-21 16:49:16.131211
5445448223	t	2025-11-07 01:30:48.357447
6532735248	f	2025-11-17 14:32:51.780218
8494703426	t	2025-12-06 14:49:55.605371
5964390462	t	2025-11-12 19:38:37.652935
5891568590	f	2025-10-26 18:57:57.423839
636735577	t	2025-12-08 10:19:49.1501
7319777571	t	2025-11-07 09:13:25.276962
6910150860	f	2025-11-11 10:35:07.584897
6520648636	t	2025-11-29 23:27:27.280176
6477484866	t	2025-10-17 14:39:02.122491
7714089439	f	2025-11-09 15:02:21.561781
8006993274	t	2025-11-15 11:23:47.161848
6588828344	t	2025-11-05 22:17:36.942738
5420999986	t	2025-12-08 14:14:38.544085
6830041427	f	2025-11-03 10:50:54.618193
8562904531	t	2025-11-27 01:30:11.123988
7441972956	t	2025-12-18 00:28:47.690108
6171495250	t	2025-12-15 21:24:34.673575
6852552336	f	2025-11-19 23:57:57.62502
5821665830	f	2025-10-24 22:09:52.431354
7123794523	f	2025-11-10 21:00:18.269903
1608543480	f	2025-11-10 21:19:42.495016
8213596906	t	2025-12-17 01:37:47.802357
7251995251	t	2025-11-02 17:40:39.650036
7433900109	f	2025-10-27 10:46:44.225731
7488003312	f	2025-11-16 12:00:37.577144
7693672756	t	2025-10-28 17:58:20.401468
8260737582	t	2025-11-16 16:53:16.111877
5848770400	t	2025-10-28 18:23:42.644351
1604618552	f	2025-10-26 17:26:13.073429
8357312111	f	2025-12-11 23:46:33.556319
6779399346	t	2025-11-10 16:15:27.338628
5387866919	f	2025-10-29 17:18:45.415259
6636522096	t	2025-10-31 15:41:11.573086
2038045502	f	2025-11-12 20:18:17.384764
7096845088	f	2025-11-13 02:47:46.081057
8373606719	t	2025-12-11 09:47:07.365269
6013957379	t	2025-12-02 17:27:31.832213
723189008	t	2025-11-03 09:23:59.154007
6305231297	t	2025-11-07 19:04:43.002418
8258901462	t	2025-12-07 02:51:41.677632
1549571710	t	2025-11-27 22:36:24.699745
7835273890	t	2025-12-14 20:09:59.658382
6490654709	t	2025-11-13 09:02:39.990743
742895166	t	2025-11-11 22:39:35.293356
8360443949	t	2025-12-16 19:50:57.366729
6366929184	t	2025-11-14 17:27:26.819023
7786809003	t	2025-12-21 20:54:17.898711
7866745942	f	2025-11-25 10:26:55.115143
6159085054	t	2025-12-16 00:12:20.045838
8431307336	t	2025-12-07 21:13:28.232641
7827652929	t	2025-12-18 00:06:25.99605
7962843287	f	2025-12-16 09:42:40.017799
8063683486	f	2025-12-17 22:59:51.341186
5406442663	f	2025-12-16 02:40:53.750281
5451735544	t	2025-12-15 00:03:09.972416
8357880060	t	2025-12-17 01:31:29.777395
7560420076	t	2025-12-15 04:04:51.018619
7452823412	t	2025-12-18 12:49:09.036124
5843862754	t	2025-12-17 03:33:37.298227
6292741991	t	2025-12-17 10:40:02.042729
5285734779	f	2025-12-17 14:28:04.956587
8388546702	t	2025-12-17 14:26:16.575161
5920013494	t	2025-12-19 05:17:30.720598
5479267800	t	2025-12-18 01:00:48.30173
7098716789	f	2025-12-18 18:23:51.568596
6876318627	t	2025-12-19 15:28:00.307789
7897782049	f	2025-12-18 18:13:29.289206
7301764474	f	2025-12-24 21:02:19.16347
1916333182	t	2025-12-19 04:57:06.945766
1931035542	t	2025-12-19 05:01:31.836641
5747969128	t	2025-12-19 05:26:55.227874
6640526724	t	2025-12-19 05:22:00.262645
5457458340	t	2025-12-19 05:31:10.605652
5794338335	t	2025-12-19 05:39:51.702632
8377242910	f	2025-12-23 20:16:49.366964
5227137974	f	2025-12-21 18:48:45.659185
7034015842	t	2025-12-21 20:36:55.857182
8547072258	f	2025-12-21 23:01:44.872238
8012129273	t	2025-12-23 22:16:32.786391
7669122337	t	2026-01-04 19:33:27.394063
6848720005	t	2026-01-01 17:19:51.73202
906648890	t	2026-01-04 19:33:34.246777
8594095910	f	2025-12-10 12:43:55.815283
5803322217	t	2026-01-01 19:46:13.746219
6396777448	f	2025-12-25 12:11:46.058552
7829152048	t	2025-12-25 16:45:18.746854
7300111554	t	2025-12-29 23:30:38.963441
1738839153	f	2025-12-15 13:24:58.134532
1444313827	t	2025-12-26 02:39:03.26534
7353874683	t	2025-12-28 17:23:32.79665
1013148420	t	2025-12-27 14:32:01.565288
6082027138	t	2025-12-27 14:32:34.385249
7238808048	t	2025-12-27 19:20:46.394442
1992060940	t	2026-01-04 19:33:40.532715
6617326165	t	2025-12-27 20:57:59.835898
1019557777	t	2025-12-27 21:31:29.459443
7885730692	t	2026-01-01 13:48:23.803068
7428775931	t	2025-12-28 10:39:24.563495
535085855	t	2025-12-31 19:41:39.935648
8288097205	t	2026-01-04 09:39:28.982684
6331543504	t	2026-01-05 09:19:15.834415
6087538623	f	2026-01-02 21:40:58.080975
6942557751	t	2025-12-29 13:16:58.579713
8431059443	t	2025-12-29 23:31:04.507659
7619204326	t	2026-01-02 05:15:48.53353
7555800019	t	2026-01-03 23:05:57.050972
5663097688	t	2026-01-05 08:28:05.622708
5081757613	t	2026-01-05 00:57:16.01053
6421644491	f	2026-01-04 11:08:17.508957
6972231926	f	2025-12-25 21:23:47.612132
8329946072	f	2025-12-26 15:08:02.983981
7500700453	t	2025-12-28 07:20:52.462106
8000547764	t	2025-12-28 08:37:50.111562
2061093227	t	2025-12-29 14:16:03.659319
625596166	t	2025-12-29 23:09:33.129692
5662756526	f	2025-12-29 23:55:40.949951
8188198606	t	2025-12-31 12:29:53.463591
7187275939	f	2025-12-31 20:34:30.452704
5112004413	t	2026-01-01 23:56:52.390531
7967694019	f	2026-01-04 09:01:22.954621
5689065087	f	2026-01-05 10:57:18.816856
\.


--
-- Data for Name: keyword_filters; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.keyword_filters (user_id, rule_id, type, keywords) FROM stdin;
1013148420	rule_706016	whitelist	{tera}
1013148420	rule_139720	whitelist	{terabox}
1013148420	rule_706225	whitelist	{terabox}
1013148420	rule_706225	blacklist	{"Too many attempts"}
1013148420	rule_309764	blacklist	{amzn}
7611856186	rule_1572025	whitelist	{/config}
7452823412	rule_680791	blacklist	{https://t.me/binance_box_channel}
7611856186	rule_1571852	whitelist	{"SIGNAL ALERT","TP1 Hit","SL Hit","TP2 Hit","TP3 Hit"}
6222156706	rule_1571946	whitelist	{"SIGNAL ALERT","TP1 Hit","SL Hit","TP2 Hit","TP3 Hit"}
6222156706	rule_1202605	whitelist	{"SIGNAL ALERT","TP1 Hit","SL Hit","TP2 Hit","TP3 Hit"}
6588828344	rule_134856	blacklist	{"Enjoy Monkey Family 🪄","Monkey Millionaire ₿"}
2012655294	rule_195606	blacklist	{@helpdesk9090}
7319777571	default	whitelist	{/blacklist_keywords}
5848770400	rule_3252653	whitelist	{(GOLD,BUY,SELL,TP,SL,Buy,Sell,Tp,Sl,Gold,NOW,Now,شراء,بيع,)}
636735577	rule_629274	blacklist	{✅,Exercise,Meditation,Trading,Discipline,Prayer,Chartink,chartink,tradingview,stocks,🔥,strategy,Strategy,ema,rsi,RsiMA,Rsi,Macd,macd,signal,holding,swing,trade,trading,liya,term,Term,Stockedge,chartink,Momentum,momentum,riding,Riding,invest,Invest,Investing,investment,asset,Asset}
6876778776	rule_761854	whitelist	{3}
6526942062	rule_804606	blacklist	{/set_options}
6532735248	rule_1597589	whitelist	{/stop_forwarding}
8069225688	rule_3675538	whitelist	{"HELLOJETKING TUSHAR"}
7835273890	rule_214257	blacklist	{https://t.me/Tirangawingo10/241476}
8329946072	rule_1249508	whitelist	{@AYLGCBot=@Official_Proofs_Bot}
6848720005	rule_1448021	blacklist	{/start}
6848720005	rule_1448198	blacklist	{"✅𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗰𝗼𝗹𝗹𝗲𝗰𝘁𝗶𝗼𝗻 = 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗰𝘂𝘀𝘁𝗼𝗺𝗲𝗿𝘀 ✅\n\n         ✅ 𝗔𝗹𝗹 𝗽𝗮𝗶𝗱","𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻𝗱 𝗯𝘂𝘆  ✅\n\n🥳𝟭.𝗦𝗻𝗮𝗽 𝗶𝗻𝘀𝘁𝗮 𝗹𝗲𝗮𝗸 ( 𝟱𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼𝘀 ✅)\n🍆𝟮. 🅒🅟 𝗸!𝗱𝘀 ( 𝟱𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼𝘀 ✅)\n⭐️𝟯.𝗥@𝗽𝗲 & 𝗳𝗼𝗿𝗰𝗲 ( 𝟱𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼𝘀 ✅)\n🍓𝟰. 𝗛𝗶𝗱𝗱𝗲𝗻 𝗰𝗮𝗺 ( 𝟰","𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼𝘀 ✅) \n⭐️𝟱. 𝘁𝗲𝗲𝗻 𝘃𝗶𝗱𝗲𝗼𝘀 ( 𝟭𝟬𝟬𝟬+ 𝘃𝗶𝗱e𝗼𝘀 ✅)\n🔥𝟲.𝗚𝗶𝗿𝗹𝘀 𝗕𝗹𝗮𝗰𝗸 𝗺𝗮𝗶𝗹 (𝟰𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼✅)\n🏃‍♂️𝟳. 𝗢𝗻𝗹𝘆 𝗳𝗮𝗻 ( 𝟭𝟬𝟬𝟬+ ✅)\n🍑𝟴. 𝗟𝗲𝗮𝗸𝘀 ( 𝟭𝟬𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼𝘀 ✅)\n🍆𝟵.𝗔𝗻𝗶𝗺𝗮𝗹𝘀 𝘄𝗶𝘁𝗵 𝗴𝗶𝗿𝗹𝘀 ( 𝟳𝟬𝟬+ 𝘃𝗶𝗱𝗲𝗼 ✅)\n❤️‍🔥𝟭𝟬. 𝗚𝗶𝗿𝗹𝘀 𝗻𝘂𝗱𝗲 𝗽𝗶𝗰𝘀 ( 𝟭𝟬𝗞 𝗣𝗵𝗼𝘁𝗼𝘀 ✅)\n🔞 𝟭𝟭. 𝗦𝗰𝗵𝗼𝗼𝗹 𝗚𝗶𝗿𝗹𝘀 ( 𝟮","𝟬𝟬𝟬+ 𝗩𝗶𝗱𝗲𝗼𝘀 ✅)\n🥵 𝟭𝟮.𝗖𝗵𝗶𝗻𝗲𝘀𝗲 𝗧𝗲𝗲𝗻 (𝟴","𝟬𝟬𝟬+ 𝗩𝗶𝗱𝗲𝗼✅)\n🤤 𝟭𝟯. 𝗦𝗵𝗲𝗺𝗮𝗹𝗲 ( 𝟮","𝟬𝟬𝟬+ 𝗩𝗶𝗱𝗲𝗼𝘀 ✅)\n🍑𝟭𝟰.𝗗𝗿𝘂𝗴𝗴𝗲𝗱 𝗴𝗶𝗿𝗹 ( 𝟱𝟬𝟬+𝘃𝗶𝗱𝗲𝗼𝘀 ✅)\n\n💎𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 (26","000+ 𝗩𝗶𝗱𝗲𝗼𝘀✅)\n\n    ➡️🛍𝗔𝗹𝗹 𝘃𝗶𝗱𝗲𝗼𝘀 𝗽𝗿𝗶𝗰𝗲 = 4999rs🛒⬅️\n    ➡️🔥𝗘𝘃𝗲𝗿𝘆 𝗼𝗻𝗲 𝘃𝗶𝗱𝗲𝗼 = 399rs🛒⬅️\n    💎𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 = 499rs 🛒⬅️\n\n   🚨𝗡𝗼 𝗙𝗿𝗲𝗲 𝗗𝗲𝗺𝗼🚨\n         \n   👉👉@best_seller_vk👈👈\n   👉👉@best_seller_vk👈👈\n\n𝘾𝙇𝙄𝘾𝙆 𝙃𝙀𝙍𝙀 𝙏𝙊 𝙒𝘼𝙏𝘾𝙃 \nDemo⤵️⤵️⤵️\nhttps://t.me/+fou2sVsly2RkMzg1\nhttps://t.me/+fou2sVsly2RkMzg1\n\n\n⬇️⬇️⬇️🔠🔠🔠 🔠🔠🔠 ⬇️⬇️⬇️\n\n    https://t.me/best_seller_vk\n    https://t.me/best_seller_vk"}
6848720005	rule_1449943	blacklist	{"https://teraboxshare.com/s/162aEXysUYsejDYJTN6Kqsw  Too many attempts","please try again later.\nhttps://teraboxshare.com/s/1F8x6TuvZJzUSNtoyrYzqiw  Too many attempts","please try again later."}
6848720005	rule_1450181	blacklist	{"Too many attempts","please try again later."}
6848720005	rule_1450317	blacklist	{"many pepole"}
7885730692	rule_1521283	blacklist	{"DM us for More Details ⬇️\n\nhttps://wa.me/message/Y3VHRA2OLLOFN1","Today's Equity Premium Call",option}
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.messages (id, user_id, message_text, message_type, created_at) FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.payments (id, user_id, plan_id, amount, payment_method, transaction_id, status, created_at, processed_at, admin_id, notes, razorpay_order_id, razorpay_payment_id, razorpay_signature, screenshot_message_id) FROM stdin;
278	6159085054	1month	99	upi	\N	approved	2025-12-15 01:28:28.376548	2025-12-15 08:09:56.839964	1013148420	\N	\N	\N	\N	2328
194	7224107415	1month	99	qr	\N	pending	2025-11-14 08:00:42.206951	\N	\N	\N	\N	\N	\N	\N
80	5891568590	1month	119	upi	\N	approved	2025-10-10 18:48:05.167718	2025-10-10 18:50:00.408538	1013148420	\N	\N	\N	\N	1136
172	7488003312	1month	99	upi	\N	approved	2025-11-03 19:35:26.229217	2025-11-03 22:09:18.527622	1013148420	\N	\N	\N	\N	1758
224	1444313827	1month	99	upi	\N	approved	2025-11-26 11:49:51.888461	2025-11-26 12:03:04.2959	1013148420	\N	\N	\N	\N	2019
210	7962843287	1month	99	upi	\N	approved	2025-11-21 19:11:54.51211	2025-11-21 20:49:09.620839	1013148420	\N	\N	\N	\N	1946
242	8566633996	1month	99	qr	\N	approved	2025-12-08 23:33:44.89791	2025-12-08 23:35:58.932275	1013148420	\N	\N	\N	\N	2177
84	5989213998	1month	119	upi	\N	approved	2025-10-12 15:56:35.993465	2025-10-12 16:02:01.855357	1013148420	\N	\N	\N	\N	1266
114	1327566897	1year	951	qr	\N	pending	2025-10-25 22:35:57.03297	\N	\N	\N	\N	\N	\N	\N
55	906648890	1month	79	\N	\N	pending	2025-09-27 11:13:46.092078	\N	\N	\N	plink_RMVyXeqj1csPYG	\N	\N	\N
142	5921486522	1month	99	paypal	\N	pending	2025-10-30 15:00:16.235549	\N	\N	\N	\N	\N	\N	\N
63	6532735248	1month	99	upi	\N	approved	2025-10-06 18:18:30.173623	2025-11-17 14:35:55.673131	1013148420	\N	\N	\N	\N	1890
270	8431059443	1month	99	\N	\N	selected	2025-12-14 09:54:32.784661	\N	\N	\N	\N	\N	\N	\N
59	7714089439	1year	1142	qr	\N	pending	2025-09-30 20:39:19.451972	\N	\N	\N	\N	\N	\N	\N
200	6570157953	1month	99	paypal	\N	pending	2025-11-17 20:15:06.647115	\N	\N	\N	\N	\N	\N	\N
116	7903348966	1month	99	paypal	\N	approved	2025-10-26 03:28:13.562373	2025-10-26 08:44:17.942385	1013148420	\N	\N	\N	\N	1574
66	8495094059	1month	119	qr	\N	rejected	2025-10-08 09:22:29.446367	2025-10-08 10:20:25.644651	1013148420	REJECTED: Unknown reason	\N	\N	\N	\N
78	7946534196	1month	119	upi	\N	pending	2025-10-10 07:54:22.804163	\N	\N	\N	\N	\N	\N	\N
152	8460919996	1month	99	paypal	\N	pending	2025-10-31 01:53:30.058167	\N	\N	\N	\N	\N	\N	\N
94	6443005862	3months	339	paypal	\N	pending	2025-10-14 20:46:27.431036	\N	\N	\N	\N	\N	\N	\N
244	6112363781	1month	99	upi	\N	approved	2025-12-08 23:57:11.599907	2025-12-09 08:26:43.835527	1013148420	\N	\N	\N	\N	2190
96	7065067748	1month	119	paypal	\N	pending	2025-10-19 21:32:25.24718	\N	\N	\N	\N	\N	\N	\N
26	775075167	1month	119	\N	\N	selected	2025-09-19 23:14:34.163242	\N	\N	\N	\N	\N	\N	\N
98	5406442663	1month	119	paypal	\N	pending	2025-10-20 11:38:53.588928	\N	\N	\N	\N	\N	\N	\N
100	6490654709	1month	119	\N	\N	selected	2025-10-21 08:15:17.614936	\N	\N	\N	\N	\N	\N	\N
178	5663097688	1month	99	qr	\N	approved	2025-11-06 16:28:51.568532	2025-12-06 08:25:51.611117	1013148420	\N	\N	\N	\N	2129
102	8126606818	1month	119	qr	\N	pending	2025-10-22 23:26:58.905836	\N	\N	\N	\N	\N	\N	\N
158	5779210849	1month	99	qr	\N	pending	2025-11-01 14:55:17.090596	\N	\N	\N	\N	\N	\N	\N
220	7238808048	1month	99	upi	\N	approved	2025-11-24 18:50:05.122814	2025-12-15 19:16:24.255189	1013148420	\N	\N	\N	\N	2351
192	7669122337	1month	99	paypal	\N	selected	2025-11-12 23:56:24.910102	2025-11-13 07:31:52.25017	1013148420	\N	\N	\N	\N	1858
104	8127965483	3months	339	paypal	\N	approved	2025-10-23 11:39:48.609708	2025-10-23 12:01:19.587908	1013148420	\N	\N	\N	\N	1503
132	8323818787	1month	99	\N	\N	selected	2025-10-27 12:49:17.108039	\N	\N	\N	\N	\N	\N	\N
154	8281707866	1year	951	qr	\N	pending	2025-10-31 05:33:20.034481	\N	\N	\N	\N	\N	\N	\N
182	5445448223	3months	283	paypal	\N	pending	2025-11-06 17:06:48.488581	\N	\N	\N	\N	\N	\N	\N
246	1019557777	1month	99	upi	\N	approved	2025-12-09 21:02:41.996258	2025-12-09 21:11:29.487884	1013148420	\N	\N	\N	\N	2217
134	8370995918	1month	99	qr	\N	approved	2025-10-27 23:53:49.476286	2025-10-28 02:49:11.956444	1013148420	\N	\N	\N	\N	1630
190	7793805367	1month	99	qr	\N	pending	2025-11-11 05:59:51.549882	\N	\N	\N	\N	\N	\N	\N
216	7301764474	1month	99	upi	\N	approved	2025-11-24 15:06:12.621551	2025-11-24 15:17:19.118363	1013148420	\N	\N	\N	\N	1988
204	6082027138	3months	283	upi	\N	approved	2025-11-17 22:28:06.646076	2025-11-17 22:32:12.751117	1013148420	\N	\N	\N	\N	1914
170	7582960557	1month	99	upi	\N	pending	2025-11-02 16:28:45.86126	\N	\N	\N	\N	\N	\N	\N
328	1612913307	1month	99	paypal	\N	pending	2025-12-24 20:46:52.180178	\N	\N	\N	\N	\N	\N	\N
284	5090523346	1month	99	upi	\N	pending	2025-12-16 14:17:21.672121	\N	\N	\N	\N	\N	\N	\N
150	1992060940	1month	99	qr	\N	approved	2025-10-30 20:36:37.634958	2025-11-30 19:00:26.668952	1013148420	\N	\N	\N	\N	2065
136	7786809003	1month	99	paypal	\N	approved	2025-10-30 14:29:29.780273	2025-12-14 14:33:33.643696	1013148420	\N	\N	\N	\N	2316
206	5803322217	1month	99	qr	\N	approved	2025-11-19 19:44:50.64562	2025-12-17 23:25:33.19256	1013148420	\N	\N	\N	\N	2432
176	7885730692	1month	99	upi	\N	approved	2025-11-05 17:30:36.656981	2026-01-01 12:28:52.415141	1013148420	\N	\N	\N	\N	2744
124	7619204326	6months	535	ton	\N	approved	2025-10-26 19:13:00.514761	2025-12-30 08:10:28.064307	1013148420	\N	\N	\N	\N	2724
222	7555800019	1month	99	upi	\N	approved	2025-11-25 08:48:21.111988	2025-12-25 08:36:42.539035	1013148420	\N	\N	\N	\N	2590
345	6594831541	3months	283	ton	\N	pending	2026-01-01 20:45:41.065166	\N	\N	\N	\N	\N	\N	\N
334	8252877204	1month	99	upi	\N	pending	2025-12-29 00:06:24.822615	\N	\N	\N	\N	\N	\N	2658
214	6848720005	1month	99	upi	\N	approved	2025-11-23 13:37:26.592309	2025-12-25 21:46:25.109806	1013148420	\N	\N	\N	\N	2608
351	7967694019	1month	99	upi	\N	approved	2026-01-03 19:29:36.380611	2026-01-03 19:40:58.319215	1013148420	\N	\N	\N	\N	2800
333	8000547764	1month	99	ton	\N	pending	2025-12-28 08:33:49.645206	\N	\N	\N	\N	\N	\N	\N
202	6421644491	1month	99	upi	\N	approved	2025-11-17 21:21:15.302668	2025-12-29 12:32:42.449915	1013148420	\N	\N	\N	\N	2701
339	5662756526	1month	99	ton	\N	pending	2025-12-30 00:00:13.109258	\N	\N	\N	\N	\N	\N	\N
240	6331543504	1month	99	ton	\N	rejected	2025-12-06 15:18:20.26484	2026-01-05 09:21:49.13442	1013148420	REJECTED: Invalid or unclear screenshot	\N	\N	\N	2820
\.


--
-- Data for Name: rules; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.rules (user_id, rule_id, name, is_active, options, manually_disabled) FROM stdin;
6087538623	rule_1894044	Num	t	{"channel_converter": {"enabled": true, "my_channel": "t.me/alfa_earnings_bot"}, "link_replacements": {"@osmlooters": "@alfa_earnings_bot", "https://t.me/osmlooters": "http://t.me/alfa_earnings_bot"}}	f
1327566897	rule_1323614	Rule SMC	t	{}	f
1013148420	rule_706016	R1	t	{}	f
1013148420	rule_706225	R2	t	{}	f
8370995918	rule_3186888	A1	t	{"forward_text_only": true, "forward_media_only": false}	f
8258901462	rule_2210712	r1	t	{}	f
5848770400	rule_3252653	Trades	t	{"forward_text_only": true, "forward_media_only": false}	f
5891568590	rule_1708905	OTHER FIRST	t	{}	f
7693672756	rule_3251577	4	t	{}	f
7467184777	rule_134942	/rules	t	{}	f
7144330602	rule_1739243	/login	t	{}	f
7488381628	rule_3517161	Automatic message	t	{}	f
7144330602	rule_1739276	Harrydevil	t	{}	f
1013148420	rule_139720	R3	t	{}	f
809117482	rule_233411	KD1	t	{}	f
7291979622	rule_416203	Signals	t	{}	f
7693090424	rule_1787862	W1	t	{}	f
7693090424	rule_1788236	1a	t	{}	f
6799961892	rule_1788421	W	t	{}	f
8282805291	rule_1453303	R1	t	{}	f
6477484866	rule_2294630	Copy trade	t	{}	f
7714089439	rule_860315	24/7 Tipping	f	{}	f
5081757613	rule_253652	Deal Forword	t	{}	f
1013148420	rule_309529	Extrape	t	{}	f
8083890417	rule_452475	R1	t	{}	f
6222156706	rule_1202605	R1	t	{"forward_text_only": true, "forward_media_only": false}	f
8064447179	rule_475987	R1	t	{}	f
7849204364	rule_1405243	R2	t	{}	f
7849204364	rule_1405271	R1	t	{}	f
8215282057	rule_1414695	E1	t	{}	f
7154763189	rule_1529434	R1	t	{"channel_converter": {"enabled": true, "my_channel": "t.me/premiumproof_bot"}, "link_replacements": {"https://t.me/+qsOy3aSmQlg3ZDE1": "@premiumproof_bot", "https://t.me/Alfa_Earning_Triks": "@premiumproof_bot"}}	f
1429618267	rule_1867318	R1	t	{}	f
6636522096	rule_3487339	R1	t	{}	f
8276262057	rule_1682557	/start	t	{}	f
8562904531	rule_1336	R1	t	{}	f
5921486522	rule_3413369	Forwarded messages	t	{}	f
6434063803	rule_920978	R1	t	{}	f
276419595	rule_3404108	Auto ff	t	{}	f
7162132327	rule_827135	/help	f	{}	f
5902304687	rule_2154230	@Priya75757	t	{}	f
6059788941	rule_1974928	R1	t	{}	f
7404167930	rule_1121253	Yashhh	t	{}	f
8343538070	rule_2012416	Rule 1	t	{}	f
7835273890	rule_214257	Registration link	t	{}	f
8127040286	rule_2161027	R1	t	{}	f
5773544941	rule_1173686	K1	t	{}	f
6942557751	rule_128212	Auto	t	{"url_preview": false, "channel_converter": {"enabled": true, "my_channel": "t.me/sujay8372"}, "forward_text_only": false, "forward_media_only": true}	f
6251096236	rule_1462816	Ashu	t	{}	f
7941190412	rule_1195275	Osm1	t	{}	f
7941190412	rule_1195456	Ak1	t	{}	f
8495094059	rule_1198121	Information	t	{}	f
8495094059	rule_1198411	Token forward	t	{}	f
8127040286	rule_2161171	/start	t	{}	f
7209556360	rule_3452808	OTP BOT	t	{}	f
5387866919	rule_2089341	Teste123	t	{"forward_text_only": true, "forward_media_only": false}	f
6651813666	rule_1797231	R1	t	{"link_replacements": {"@osmlooters": "@premiumproof_bot\\n\\nhttps://t.me/+ -> @premiumproof_bot", "https://t.me/": "@premiumproof_bot", "https://t.me/+": "@premiumproof_bot", "https://t.me/osmlooters": "@premiumproof_bot", "https://t.me/+qsOy3aSmQlg3ZDE1": "@premiumproof_bot"}}	f
6331543504	rule_3430271	A1	f	{"text_replacements": {"HELLO": "GG", "@amfbot_admin": "Ss"}}	f
7611856186	rule_1571852	R1	t	{}	f
6617326165	rule_299365	TMW	t	{}	f
7431619619	rule_3599845	R1	t	{}	f
6654944138	rule_1602200	KINGDARK	t	{}	f
5891568590	rule_1616422	OTHER	t	{}	f
8006768154	rule_2189350	R1	t	{}	f
8224373261	rule_2196849	Anime	t	{}	f
5389796957	rule_3607326	Golden Results forwarding	t	{}	f
6532735248	rule_1597589	R1	t	{"link_replacements": {"@THUNDER_X_OWNER_BOT": "@premiumproof_bot", "http://T.me/PTMCASHHELP": "@premiumproof_bot"}}	f
7251995251	rule_2566221	Hakaj	t	{}	f
5023503076	rule_2663138	New	t	{"forward_text_only": false, "forward_media_only": false}	f
8126606818	rule_2754801	/start	t	{}	f
5821665830	rule_2922360	/source	t	{}	f
8012257232	rule_2817684	R1	t	{}	f
7903348966	rule_3046200	/source	t	{"forward_text_only": true, "forward_media_only": false}	f
1013148420	rule_309764	extrape2	t	{"remove_links": false}	f
6529663543	rule_2978426	https://t.me/interlinkIDchat	t	{}	f
8323818787	rule_3146502	R1	t	{}	f
6490654709	rule_3000381	Market	t	{}	f
7433900109	rule_3139397	ADITYA	t	{}	f
8127965483	rule_3147250	Xauusd	t	{}	f
5748157494	rule_3149973	R1	t	{}	f
8358336845	rule_80397	Ayaan	t	{}	f
7841164931	rule_354659	My channel forwed	t	{}	f
6806206534	rule_688987	Forward	t	{}	f
6171495250	rule_343254	Deals	t	{}	f
7962843287	rule_358910	R5	t	{}	f
1414116736	rule_351459	R1	t	{}	f
8106692932	rule_1839524	R1	t	{}	f
8040370079	rule_424689	Sn1	t	{}	f
6514739688	rule_119597	RULE	t	{}	f
8357880060	rule_443947	ValenceCrypto	t	{}	f
1992060940	rule_1895892	Anime	f	{"forward_text_only": false, "text_replacements": {"@Animee_4u": "@TeluguXAnime"}, "forward_media_only": true}	f
7669122337	rule_2490482	R2	f	{}	f
906648890	rule_571886	B1	t	{}	f
7669122337	rule_2488327	R1	t	{}	f
7786809003	rule_242682	R3	t	{"remove_links": true, "text_replacements": {"[Trade in  — first trading terminal with real-time market map]( | [Chart](\\n\\n⚡️[": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@snapcoin2", "Trade in karta.trade — first trading terminal with real-time market map | Chart\\n\\n⚡️atm.day": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa mudane and marwo 🌟\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@kingtoronto"}}	f
7786809003	rule_243020	R4	t	{"remove_links": true, "text_replacements": {"Trade on BONKbot | CHART\\n⚡️atm.day": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa mudane and marwo 🌟\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@kingtoronto", "[Trade on BONKbot]( | [CHART](\\n⚡️[": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@snapcoin2"}}	f
7635975214	rule_821313	Rinku78	t	{}	f
7353874683	rule_842862	source	t	{}	f
7047677983	rule_5484	R1	t	{}	f
7162132327	rule_662429	X8	t	{}	f
8360443949	rule_299453	Auto	t	{"url_preview": false, "channel_converter": {"enabled": true, "my_channel": "t.me/sujay8372"}, "forward_text_only": false, "forward_media_only": true}	f
6013957379	rule_500083	/config	t	{}	f
6521860950	rule_314698	R1	t	{}	f
7786809003	rule_243133	R5	t	{"remove_links": true, "text_replacements": {"Trade in karta.trade — first trading terminal with real-time market map | Chart\\n\\n⚡️atm.day": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa mudane and marwo 🌟\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@kingtoronto", "Links:\\n[ | [Website]( | [Twitter](\\n\\n[Trade in  — first trading terminal with real-time market map]( | [Chart](\\n\\n⚡️[": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@snapcoin2"}}	f
8288097205	rule_42011	Auto	t	{"url_preview": false, "channel_converter": {"enabled": true, "my_channel": "t.me/sujay8372"}, "forward_text_only": false, "forward_media_only": true}	f
7786809003	rule_243252	R6	t	{"remove_links": true, "text_replacements": {"[Trade in GMGN](\\n\\n[⚡️": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@snapcoin2", "Trade in GMGN\\n\\n⚡️atm.day": "#Snap.coin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa mudane and marwo 🌟\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@kingtoronto"}}	f
5406442663	rule_362648	Luia signal	t	{}	f
7786809003	rule_333451	R7	t	{"url_preview": true, "remove_links": true, "text_replacements": {"[Trade on BONKbot]( | [CHART](\\n[⚡️Early access to Telemetry by BONKbot to execute your trading srtrategy](\\n\\n[⚡️": "ka daxadar walal"}}	f
6889190828	rule_652920	R1	t	{}	f
5090523346	rule_403738	/rules	t	{"forward_text_only": false, "forward_media_only": false}	f
7844185193	rule_120843	R1	t	{}	f
6112363781	rule_137204	/source	t	{}	f
6216309591	rule_414976	R1	t	{}	f
8213596906	rule_444635	ValenceCrypto	t	{}	f
5843862754	rule_451484	R1	t	{}	f
5907554483	rule_452727	Valence Crypto	t	{}	f
8594095910	rule_36683	News	t	{"url_preview": true, "channel_converter": {"enabled": true, "my_channel": "t.me/Chinoz_kanali"}}	f
6292741991	rule_477180	SantaBNB	t	{"forward_text_only": false, "forward_media_only": false}	f
1738839153	rule_307630	/source	t	{"forward_text_only": false, "forward_media_only": false}	f
5285734779	rule_477746	NEW_	t	{"forward_text_only": false, "forward_media_only": false}	f
6082027138	rule_333452	R1	t	{}	f
7713662771	rule_479913	1	t	{}	f
5479267800	rule_528858	Valence	t	{}	f
7827652929	rule_525672	Valence Crypto	t	{}	f
7441972956	rule_526198	Valence C	t	{}	f
7897782049	rule_584660	/help	t	{}	f
6640526724	rule_628749	77	t	{}	f
1916333182	rule_629316	77	t	{}	f
1931035542	rule_629578	77	t	{}	f
5920013494	rule_630475	77	t	{}	f
6876778776	rule_761854	Poed	t	{}	f
8431307336	rule_230046	Uzbekistan	t	{"url_preview": true, "channel_converter": {"enabled": true, "my_channel": "t.me/Uzbekistan24tezkor"}}	f
7796576246	rule_3623961	no sender name	t	{}	f
8189961029	rule_208072	First	t	{}	f
6526942062	rule_804606	Bobysansi	t	{}	f
8069225688	rule_3675538	R1	t	{}	f
7582960557	rule_3675804	R1	t	{}	f
1444313827	rule_511409	METRO 45,60	t	{}	f
7866745942	rule_1813541	HAHA	t	{}	f
5332226638	rule_3699972	Pradeep	t	{}	f
723189008	rule_3733604	Trading	t	{"forward_text_only": false, "forward_media_only": false}	f
636735577	rule_629274	R1	t	{}	f
7224107415	rule_864307	debulae	t	{}	f
2012655294	rule_195606	Auto message forward	t	{"forward_text_only": false, "forward_media_only": false}	f
7300111554	rule_216260	/remove_source	t	{}	f
1700711970	rule_9774	Trading	t	{}	f
5445448223	rule_240672	1	t	{}	f
6818938551	rule_425990	https://youtube.com/shorts/GSlC5pwxFkQ?si=mXUK1PPm-RJzS8hl	t	{}	f
6305231297	rule_303725	Rt	t	{}	f
6027932766	rule_66773	/rules	t	{}	f
7174833388	rule_101659	/source	t	{}	f
8280548411	rule_110584	PETER	t	{}	f
7246249229	rule_426101	Hii	t	{}	f
5663097688	rule_209096	Target 2	f	{}	f
7555800019	rule_1807764	R1	t	{}	f
906648890	rule_571989	/subscription	f	{}	f
7488003312	rule_3782901	/start_forwarding	t	{"remove_links": true, "channel_converter": {"enabled": true, "my_channel": "t.me/CODE_LOOTERS_PROOF_BOT"}}	f
6588828344	rule_134856	Ff	t	{"forward_text_only": true, "forward_media_only": false}	f
6366929184	rule_895029	forward rule	t	{}	f
7065067748	rule_919674	Di	t	{}	f
6306052652	rule_467191	Botmaster55	t	{}	f
8382351343	rule_933468	/rules	t	{}	f
5451735544	rule_265425	1	t	{}	f
404962727	rule_265476	A	t	{}	f
7811318319	rule_990550	/source	t	{}	f
7560420076	rule_108595	R1	t	{"forward_text_only": true, "forward_media_only": false}	f
742895166	rule_502088	7777	t	{}	f
5689065087	rule_536552	Sanam	t	{}	f
6779399346	rule_550914	R1	t	{}	f
6078490717	rule_558274	/login	t	{}	f
6159085054	rule_265926	Auto Forward	t	{"text_replacements": {"original_News | Markets | YouTube": "replacement_Follow for daily latest Crypto News🗞️"}}	f
7452823412	rule_680791	R1	t	{"url_preview": false, "forward_text_only": false, "link_replacements": {"https://t.me/binance_box_channel": "https://t.me/CryptosboxX"}, "forward_media_only": false}	f
6271999767	rule_1891516	Karma	t	{}	f
7962843287	rule_1546985	/delete_rule	f	{}	f
7430101095	rule_672142	R1	t	{}	f
7880089937	rule_690508	A	t	{}	f
5964390462	rule_706573	R1	t	{}	f
7752022043	rule_722960	R1	t	{}	f
8260737582	rule_1068508	sabrina	t	{}	f
6570157953	rule_1164447	/config	t	{}	f
6551218990	rule_1235124	LUCAS BETTING FORWARDING	t	{}	f
8243850085	rule_1314518	FREE	t	{}	f
5445031425	rule_1334710	R1	t	{}	f
7636116711	rule_1491584	91Club 30rs	t	{"channel_converter": {"enabled": true, "my_channel": "t.me/flash_users_bot"}}	f
8281707866	rule_1557538	/set_rule	t	{}	f
8494703426	rule_831899	1	t	{}	f
535085855	rule_332600	Satdev Group	t	{}	f
8566633996	rule_59028	/set_rule	t	{}	f
625596166	rule_211950	Send all files	t	{"forward_text_only": false, "forward_media_only": false}	f
1019557777	rule_212814	Send all files	t	{}	f
7301764474	rule_330535	MAIN	t	{"remove_links": false}	f
8357312111	rule_6238	R1	t	{}	f
7786809003	rule_242224	R1	t	{"remove_links": true, "text_replacements": {"[Trade on BONKbot]( | [CHART](\\n[⚡️Early access to Telemetry by BONKbot to execute your trading srtrategy](\\n\\n[⚡️": "#Snapcoin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii caawi mad ah waku diyaar 24/7 \\n@snapcoin10"}}	f
8063683486	rule_521570	Send	t	{}	f
5803322217	rule_526652	ValenceCrypto	t	{}	f
7829152048	rule_527237	valencecrypto	t	{}	f
7428775931	rule_527822	ValenceCrypto	t	{}	f
7098716789	rule_591291	/subscription	t	{}	f
5747969128	rule_631076	Vc	t	{}	f
5457458340	rule_631366	Vc	t	{}	f
5794338335	rule_631776	Vc	t	{}	f
6876318627	rule_666944	first	t	{}	f
487621983	rule_687069	Forward	t	{}	f
8450125934	rule_702337	Promo Gucci	t	{}	f
8243249885	rule_770114	Kkrule	t	{}	f
7337643152	rule_779226	Rt	t	{}	f
8431059443	rule_782064	Loot offer	t	{}	f
7238808048	rule_847843	1	t	{}	f
7238808048	rule_847866	2	t	{}	f
5227137974	rule_851637	Hardik	t	{"forward_text_only": false, "forward_media_only": false}	f
5663097688	rule_208249	Target	t	{}	f
6331543504	rule_1334118	A2	t	{"remove_links": false, "replace_all_text": {"enabled": true, "replacement": "it's been sent"}}	f
1992060940	rule_1677556	Mv Database	t	{}	f
1992060940	rule_302840	Series	f	{"text_replacements": {"@piroxbots": "@MoviieBuzzz", "@piro_files": "@MoviieBuzzz", "@MS_LinkZzzz": "@MoviieBuzzz", "@TG_Movies4u": "@MoviieBuzzz", "@KumarValimaiOfclOG": "@MoviieBuzzz"}}	f
7034015842	rule_858214	91Club	t	{}	f
7786809003	rule_857969	R2	t	{"remove_links": true, "text_replacements": {"[Trade on BONKbot]( | [CHART](\\n[⚡️Early access to Telemetry by BONKbot to execute your trading srtrategy](\\n\\n[⚡️": "#Snapcoin Waa Furaha guushada 💸🍀\\n\\n🔑 Albaabka nasiibka furihiisu waa adkaysi\\n\\n• Guul iyo nasiib wanaagsan ayaan kuu rajaynayaa 🌟🤑\\n\\n\\nWixii cawi mad ah waku diyaar 24/7 \\n@snapcoin10"}}	f
8547072258	rule_865107	KK	t	{"forward_text_only": false, "forward_media_only": false}	f
8012129273	rule_1036761	/start_forwarding	t	{}	f
1612913307	rule_1117143	BETSOPT	t	{}	f
6396777448	rule_1173123	molu	t	{}	f
7656004679	rule_1200589	Nik	t	{}	f
8329946072	rule_1249508	A1	t	{}	f
6031182200	rule_1292813	Signal	t	{}	f
2061093227	rule_1306930	R1	t	{}	f
7617682298	rule_1543974	/set_rule	t	{}	f
6421644491	rule_225354	Forward	t	{"remove_links": true}	f
8586830891	rule_227291	@ Goodday bro~ Do you get any confirmed corporate account? If you have it then let me know. We will do the testing today and start the work from tomorrow.\n\nLX PAY💳💳\n🔤 🔤 🔤 🔤 🔤 🔤\n           \n\n🤩Our company offers a high percentage job with a rate of 3.2% to 3.5%.🤩\n\nUrgent Notice\n🤩reward of 20K  inr-80K inr\n🤩reward of 20K  inr-80k inr\n🤩reward of 20K  inr-80k inr\n\nThere is no need to wait. The beneficiary takes effect immediately and starts working. High %.\nRun the full account limit every day\n\n➖➖➖➖➖➖➖\nWITHOUT DEPOSIT ⬇️\n➖➖➖➖➖➖➖➖\n\n✅RazorpayX RBL VPA activated with mqr\n✅BOM corporate/retail with mqr🤩\n✅IDBI corporate/retail with mqr\n✅DBS Ideal Corporate bank with mqr\n✅RBL corporate account   with mqr🤩\n✅CUB (City Union Bank)corporate/retai with mqr\n✅ICIC corporate with mqr \n✅IOB corporate with mqr\n✅Dhanlaxmi corporate with mqr\n✅INDIAN BANK  with mqr -TEST\n✅SOUTH INDIAN BANK corporate with mqr -TEST\n✅SBM Bank India with mqr -TEST\n✅ KGB (Kerala Gramin Bank) with mqr\n\nPAY OUT FUND 💹\n\n\n1⃣Razorpay X + RBL\n2⃣DBS IDEAL\n3⃣ HDFC with Domain Snorkel\n4⃣Yesbank Corporate 1-5 Cr limit\n5⃣ SBI CMP\n6⃣ Yes business with bulk limit - 1-5 Cr limit\n7⃣ Federal one 1-5Cr limit\n8⃣Bandhan Corporate 1-5Cr limit\n9⃣FED ONE	t	{}	f
7500700453	rule_1384049	News	t	{"channel_converter": {"enabled": true, "my_channel": "t.me/Chinoz_kanali"}}	f
8000547764	rule_1418446	/source	t	{"forward_text_only": false, "forward_media_only": false}	f
6848720005	rule_1448114	3	t	{}	f
6848720005	rule_1448198	4	t	{}	f
6848720005	rule_1449885	7	t	{}	f
6848720005	rule_1449943	8	t	{}	f
6848720005	rule_1450102	9	t	{}	f
6848720005	rule_1450181	10	t	{}	f
6848720005	rule_1450242	11	t	{}	f
8252877204	rule_1458612	Always share all updates in all groups	t	{}	f
6848720005	rule_1450317	12	t	{"forward_text_only": false, "forward_media_only": false}	f
8188198606	rule_1691815	Hello	t	{}	f
5662756526	rule_1560286	😀Telegram stars  olib beramiz🌟\n\n⭐100 stars 22 ming som😀\n\n⭐200 stars 43 ming som😀\n\n⭐500 stars 110 ming som✅\n\n⭐1000 stars 215 ming som✅\n\n❗️Minum 100 stars⭐\n\n⭐Telegram premium ham oberamiz⭐\n\n💜1 oylik 40 ming som (akk krib⭐\n\n💜3 oylik 160 ming som (akk krmasdan)⭐\n\n💜6 oylik 220 ming som (akk krmasdan)⭐\n\n💜1 yilik 290 ming som (akk krb)⭐\n\n💜1 yilik  360 ming som (akk krmasdan)⚡\n\n🧑🏻‍💻Murojaat uchun: @iiBobur📞	t	{}	f
8005019736	rule_186380	Devesh Raikwar	t	{}	f
8257807182	rule_214400	Rule	t	{}	f
7885730692	rule_1521283	/source	t	{"remove_links": true, "channel_converter": {"enabled": true, "my_channel": "t.me/thewealthgeniuscommunity"}, "link_replacements": {"@Share_Market_Information_1": "https://t.me/thewealthgeniuscommunity"}}	f
8533537899	rule_1702735	R1	t	{}	f
7815565723	rule_1705886	R1	t	{}	f
6729691597	rule_1722126	.	t	{}	f
7792750331	rule_30964	ROHAN	t	{}	f
5604698232	rule_35634	linek111	t	{}	f
6848720005	rule_38028	14	t	{}	f
6848720005	rule_38098	15	t	{}	f
6848720005	rule_38176	16	t	{}	f
6848720005	rule_38211	17	t	{}	f
6848720005	rule_37984	13	f	{}	f
8377242910	rule_215385	R2	t	{}	f
5112004413	rule_40037	Forword	t	{"channel_converter": {"enabled": true, "my_channel": "t.me/DiscountLinkHub"}, "link_replacements": {"t.me/lootshoppingxyz": "t.me/DiscountLinkHub"}}	f
6594831541	rule_50544	/destination	t	{}	f
7619204326	rule_1688614	Meme	t	{"forward_text_only": true, "forward_media_only": false}	f
\.


--
-- Data for Name: sources; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.sources (user_id, chat_id, title, rule_id, username) FROM stdin;
8495094059	8346709989	Advance Auto Messege Forwarder Bot	rule_1198121	advauto_messege_forwarder_bot
8431059443	-1002125169945	King Deals	rule_782064	\N
8370995918	-1001385136844	🇮🇳 🔝 🎮INDIAN TOP GAMES🇮🇳 🔝 🎮	default	\N
6222156706	-1002154812244	The Gold Complex	rule_1202605	\N
8370995918	-1001385136844	🇮🇳 🔝 🎮INDIAN TOP GAMES🇮🇳 🔝 🎮	rule_3186888	\N
1327566897	-1001542989341	ENTWA SMC TRADING	rule_1323614	\N
1327566897	-1001562662042	ENTWA TRADING VIP	rule_1323614	\N
1013148420	-1001102567094	Godi Me Lelo 🥵🔥	default	\N
1013148420	-1002291081494	TeraFilm	default	\N
1013148420	-1002348837245	✨Love Dose✨	default	\N
1013148420	-1001102567094	Godi Me Lelo 🥵🔥	rule_706016	\N
1013148420	-1002291081494	TeraFilm	rule_706016	\N
7154763189	-1003154540614	CHECK ️️	rule_1529434	\N
2012655294	-1002544838211	PREMIUM SHARE MARKET CALL	rule_195606	\N
7154763189	-1002020680830	3 SITE DAILY RS.120 CODE	rule_1529434	\N
1013148420	5762616457	LinkConvertTeraBot	rule_706225	LinkConvertTerabot
742895166	-1003108577262	EGurukul Backup	rule_1435917	\N
1013148420	-1002505839345	🥵𝙲𝙾𝙻𝙻𝙰𝙶𝙴 𝚅𝙸𝚁𝙰𝙻 𝚅𝙸𝙳𝙴𝙾 🥵	rule_706016	\N
5663097688	240044026	IFTTT	rule_208249	IFTTT
7467184777	-1003073239955	Car	default	\N
7693672756	-1002002553536	@BD_Trading_Bot	rule_3251577	\N
7319777571	-1001739246759	Share market call (SEBI REG.)	default	\N
8215282057	7814203456	Pvc	rule_1414695	\N
5663097688	240044026	IFTTT	rule_209096	IFTTT
7611856186	-1003006520508	Test1	rule_1571852	\N
1013148420	8324819345	tg forwarder	rule_139720	tg2forwarder_bot
809117482	-1001174144067	CoolzTricks Official - Deals & Offers	default	\N
809117482	-1001111080840	All Hindi Tech	default	\N
809117482	-1001853245911	Cashback Time	default	\N
8126606818	8346709989	Advance Auto Messege Forwarder Bot	rule_2754801	advauto_messege_forwarder_bot
8126606818	8366789774	Advance Auto Messege Forwarder Payment Bot	rule_2754801	advance_forwarder_payment_bot
5081757613	690321302	Biltu	default	\N
8126606818	-1003122579161	Dono	rule_2754801	\N
6532735248	-1002206619252	OKWIN✨VIP✨PREDICTIONS 🎯	rule_1582143	\N
8127040286	-1001915606317	WSOTP	rule_2161171	\N
5081757613	-1001213232901	🎉UttamX360 Loot Deals Offers 📌 🏷 | Best Daily Deals offers 😍 | India Daily LIVE Deals	rule_253652	\N
8127040286	-1002055246264	Dubai News 365 / أخبار دبي / দুবাই সংবাদ / Дубай Новости / Noticias de Dubái / 杜拜新聞	rule_2161171	\N
1013148420	2015117555	ExtraPe Link Converter Bot (Official)	rule_309529	ExtraPeBot
1013148420	-1001389782464	ExtraPe | Earn By Sharing Deals	rule_309764	\N
8083890417	8346709989	Advance Auto Messege Forwarder Bot	rule_452475	advauto_messege_forwarder_bot
8083890417	-1001417241897	Free 1k subscriber in 1 month Youtube	rule_452475	\N
8083890417	-1001758792916	Free 1k you tube subscriber	rule_452475	\N
8083890417	6927826008	Yash	rule_452475	\N
8083890417	-1002039354699	Tech Editz	rule_452475	\N
6654944138	7533758507	CALLBOMBER NET	rule_1602200	callbombernet_bot
8064447179	-1001474081644	INDIAN SUB 4SUB YOUTUBER	rule_475987	\N
8064447179	-1001820393936	YOUTUBE FREE SUBSCRIBER 1K SUBSCRIBER 4K WACHTIME	rule_475987	\N
8064447179	-1002357057872	Subscribe Exchange Free 2024	rule_475987	\N
8064447179	-1001217282906	YOUTUBE SUB4SUB GROUP	rule_475987	\N
8126606818	777000	Telegram	rule_2754801	\N
906648890	-1002406130108	Editverse OG	rule_571886	\N
8126606818	-1003043888264	Backup demo	rule_2754801	\N
7162132327	-1002802768022	𝐔𝐍𝐊𝐍𝐎𝐖𝐍 𝐕𝐈𝐏 😈	rule_662429	\N
8224373261	-1002905021619	Anime database	rule_2196849	\N
8343538070	-1002988084961	BWT 00:10	rule_2012416	\N
8012257232	-1002942055774	Algo Pips VIP Signal Service	rule_2817684	\N
7636116711	-1002149439821	𝟗𝟗.𝟗%𝗦𝗨𝗥𝗘 𝗦𝗛𝗢𝗧 𝗙𝗥𝗘𝗘	rule_1491584	\N
6434063803	-1001567949436	SUPER TIPS 👑	rule_920978	\N
8258901462	-1001728487830	Quotex_SuperBot	rule_2210712	\N
1013148420	-1001446956910	Loot Alerts	rule_309764	\N
6490654709	-1002609521554	Market Update & News | Hello Traders	rule_3000381	\N
7404167930	-1001945619495	Offer Bazaar	rule_1121253	\N
7337643152	7066339174	🦅𝑸𝑨𝒁𝑨𝑿𝑳𝑰🦅	default	\N
7903348966	-1002544327602	Crazy Goat (UTC -3)	rule_3046200	\N
7903348966	-1001197297384	Maythous Calls	rule_3046200	\N
6532735248	-1002020680830	3 SITE DAILY RS.120 CODE	rule_1432510	\N
5773544941	-1002712411164	Master Loots Chat	rule_1173686	\N
7941190412	-1001936312950	COOE (RXCE) Crypto	rule_1195275	\N
6477484866	-1002366811742	SE CAPITAL ACADEMY VIP	rule_2294630	\N
6651813666	-1002020680830	3 SITE DAILY RS.120 CODE	rule_1797231	\N
8282805291	-1002990867459	પ્રગતિ 4	rule_1453303	\N
8224373261	-1002810916133	Movie db	rule_2196849	\N
6651813666	-1003154540614	CHECK ️️	rule_1797231	\N
7693090424	-1002134775752	𝐄𝐀𝐑𝐍𝐈𝐍𝐆 𝐖𝐈𝐓𝐇 𝐒𝐀𝐌	rule_1787862	\N
6799961892	-1002981934268	Y	rule_1788421	\N
7238808048	-1002547369769	Joinnnn	rule_847843	\N
7251995251	-1003186537080	Doc tutorial Backup	rule_2566221	\N
7238808048	8236128760	@LinkConvertTerabot	rule_847866	LinkConvertTera3bot
7669122337	-1003173166911	memecoin trading	rule_2490482	\N
6551218990	-1002663458928	LUCAS MATHIAS FIXED ⚽️🥎	rule_1235124	\N
7786809003	7710129239	atm.day — OG algo v.2.0	rule_857969	atmogbeta_bot
5023503076	-1001162527682	प्राकृत गृहकार्य मात्र	rule_2663138	\N
5445448223	-1002930067925	𝙆𝙖𝙛𝙠𝙖 • CC刮刀	rule_240672	\N
5848770400	-1002186209306	نادي المخبز لتمارين عضل 💵	rule_3252653	\N
7301764474	-1002198749800	Siva Looters (Official)	rule_330535	\N
7560420076	-1001985222102	💢 Telegram Group Channel Links 💢	rule_108595	\N
5821665830	-1002919863129	Khan Sir Foundation	rule_2922360	\N
7903348966	-1002421215845	Bullish Calls - BSC	rule_3027426	\N
7903348966	-1002483474049	SolHouse Signal	rule_3046200	\N
7903348966	-1002421215845	Bullish Calls - BSC	rule_3046200	\N
7903348966	-1003002694443	Bomet on Base	rule_3046200	\N
7903348966	-1002380238568	APE Trump AI 💥|UTC -3|	rule_3046200	\N
7903348966	-1001614368274	BATMAN GAMBLE 🦇	rule_3046200	\N
7903348966	-1002444918055	Ivan shiller 🃏🎴	rule_3046200	\N
7903348966	-1001758611100	Gambles 🎲 MadApes	rule_3046200	\N
7903348966	-1002439065692	OG Figaro Degen 🚀🎰	rule_3046200	\N
7903348966	-1002339285575	1000x gem 👁️‍🗨️	rule_3046200	\N
7903348966	-1002592367917	BONK Gamble	rule_3046200	\N
7903348966	-1001873505928	@TRENDING (ETH / SOL)	rule_3046200	\N
7903348966	-1002745256661	Niño Alpha	rule_3046200	\N
7903348966	-1002379242756	Medz Lab 🇭🇰	rule_3046200	\N
7903348966	-1002216388730	Persian Cooks	rule_3046200	\N
7903348966	-1002457923282	Jim Davos 🇮🇱	rule_3046200	\N
7903348966	-1002054466090	Cas Gem	rule_3046200	\N
7903348966	-1002161078179	Chen's Gambles	rule_3046200	\N
7903348966	-1001697697574	MadApes Calls	rule_3046200	\N
7903348966	-1002184958939	BING-SUPER-CALL	rule_3046200	\N
7903348966	-1002121809180	sidelined calls (redemption)	rule_3046200	\N
7903348966	-1001955928748	XAce Calls - Multichain	rule_3046200	\N
7903348966	-1002482272712	Diamond Degens	rule_3046200	\N
7903348966	-1002486135990	Kaito AI Calls	rule_3046200	\N
7903348966	-1001510769567	🦇 BATMAN GAMBLE 🎲	rule_3046200	\N
7903348966	-1002622682621	BscHouse Signal	rule_3046200	\N
7903348966	-1001523523939	Degen Seals	rule_3046200	\N
7903348966	-1002008359812	Robinson Degens	rule_3046200	\N
7903348966	-1001810124798	Maestros Gamble Degen Apes	rule_3046200	\N
7903348966	-1002444165371	SKULL FINANCE GAMBLE 🃏	rule_3046200	\N
7903348966	-1002486541336	The Decus Gamble 💠💮	rule_3046200	\N
7903348966	-1002285320131	Anderson 100x Gem	rule_3046200	\N
7903348966	-1002380267904	Risk to Rich	rule_3046200	\N
7903348966	-1002032946187	Solstice's Moonshots	rule_3046200	\N
7903348966	-1002756536009	Charm.Play	rule_3046200	\N
7903348966	-1002730478294	Atlantic Ocen 🧩	rule_3046200	\N
7903348966	-1002664459514	CATZ CALL	rule_3046200	\N
7903348966	-1002213604525	Rocco’s Plays 🎯	rule_3046200	\N
7903348966	-1001655443406	Micha 电话 - Multichain	rule_3046200	\N
7903348966	-1002980057046	MikzCooksss	rule_3046200	\N
7903348966	-1001990117454	Spaceman Callz Solana	rule_3046200	\N
7903348966	-1002560469130	Moon or Rug	rule_3046200	\N
7903348966	-1001998961899	💎 GemTools 💎 Calls	rule_3046200	\N
7903348966	-1002510336186	Alfa 100x signals	rule_3046200	\N
7903348966	-1001927494975	Chigga's Gambles 赌博日记	rule_3046200	\N
7433900109	-1002885460100	BOT TESTING	rule_3139397	\N
6818938551	777000	Telegram	rule_425990	\N
8281707866	-1001262300473	Blockchain Usa Official ( Binance ) 🐋	rule_1557538	\N
6331543504	-4949991397	Testgroup	rule_3430271	\N
8069225688	-1002093949704	🚀 LUCKYJET BY JETGOD 🚀	rule_3675538	\N
723189008	-1003076424120	Yash Trading PAID	rule_3733604	\N
1700711970	-1002750423414	Equinox Trading Sphere	rule_9774	\N
5227137974	8424929012	Renamer 8GB | SRC	rule_851637	The_Renamer_Robot
7034015842	7554521137	𝙆𝙖𝙪𝙨𝙝𝙞𝙠 𝙖𝙧𝙘𝙝𝙞𝙩	rule_858214	\N
8127965483	-1003199310757	XAUUSD Trades	rule_3147250	\N
5748157494	-1003152600742	Chat -1003152600742	rule_3149973	\N
8533537899	-1003629179518	ZAP PAY	rule_1702735	\N
6087538623	-1001798214845	Think Success 💸🚀	rule_1894044	\N
7714089439	-1001567949436	SUPER TIPS 👑	rule_860315	\N
6305231297	-1001513290450	GETMODPC	rule_303725	\N
5921486522	-5092049441	V	rule_3413369	\N
7209556360	-1003165111567	OTP	rule_3452808	\N
6636522096	-1001232298514	PepeChannel	rule_3487339	\N
6830041427	-1002187486229	All Yono Promo Code	rule_3506946	\N
7488381628	7488381628	𝘼𝙍𝙊𝙃𝙄 🌷	rule_3517161	\N
7815565723	-1001824768901	komal_hotty_real sab ki darling	rule_1705886	\N
5112004413	-1002140128004	🛍 Loot Deals Kart 🛒	rule_40037	\N
8257807182	-1003693662050	FIRE TOON TAMIL ✨	rule_214400	\N
6421644491	-1002059742538	55 Club VIP Group 💰	rule_225354	\N
6421644491	-1002526573646	In 999 Official VIP	rule_225354	\N
6421644491	-1001741296441	91 Club Sure Prediction	rule_225354	\N
7796576246	-1002002220719	MEGAOTT FIXTURES AND EVENTS	rule_3623961	\N
6027932766	-1002117146781	𝐋𝐀𝐓𝐄𝐒𝐓 𝐌𝐎𝐕𝐈𝐄	rule_66773	\N
6588828344	-1002225791887	Monkey Millionaire ₿	rule_134856	\N
742895166	-1003377456511	DAMS B2B 2025 BACKUP	rule_502088	\N
7786809003	-5094793695	Test_admin	rule_242682	\N
6779399346	-1001567949436	SUPER TIPS 👑	rule_550914	\N
8012129273	-1003263659514	S 1	rule_1036761	\N
8431307336	-1001450792566	O'zbekiston 24	rule_230046	\N
649455144	-1001389782464	ExtraPe | Earn By Sharing Deals	default	\N
1414116736	-1001905260504	15939 MPPSC 2023 One Year (Sampoorn Hindi) Batch (From Classroom) (UTKARSH).text	rule_351459	\N
6306052652	-1002539937252	Databases fotik	rule_467191	\N
1992060940	-1001543052371	DATABASE 1	rule_1677556	\N
7430101095	-1002121418673	𝟗𝟖% 𝐀𝐂𝐂𝐔𝐑𝐀𝐓𝐄 𝐆𝐎𝐋𝐃 𝐒𝐈𝐆𝐍𝐀𝐋𝐒 𝐒𝐔𝐑𝐄	rule_672142	\N
6013957379	-1002115686230	Pump Alert - GMGN	rule_500083	\N
5964390462	-1001093093387	Light of the Truth ©	rule_706573	\N
7752022043	8402260817	Ms_Puiyii 💕	rule_722960	Ms_Puiyii_bot
8276262057	-1002844530943	Parsian Manga archive gp	rule_1682557	\N
7786809003	7621472519	atm.day — OG Algo	rule_235523	atmogalgo_bot
7786809003	7621472519	atm.day — OG Algo	rule_242224	atmogalgo_bot
1444313827	-1003391891155	mib tv	rule_511409	\N
7786809003	7822692800	atm.day — pump.fun algo	rule_242682	atmpumpfun_bot
7786809003	8118238194	atm.day — Raydium LaunchLab & BonkFun algo	rule_243020	atmlaunchlab_bot
6521860950	-1002579610926	The premium	rule_314698	\N
530131604	-5081370219	Lybozping	default	\N
636735577	-1002931679350	Focus & Consistency	rule_629274	\N
7669122337	-1003173166911	memecoin trading	rule_2488327	\N
7866745942	-1002775572698	YONO_HOST	rule_1813541	\N
8106692932	7261479507	Jaspreet	rule_1839524	\N
6271999767	-1001685029638	𝑻𝒓𝒂𝒅𝒊𝒏𝒈 𝑽𝒊𝒆𝒘	rule_1891516	\N
6366929184	-1001423395942	Free Earning Tech	default	\N
1992060940	-1002143874316	ANIMEE 4U TELUGU	rule_1895892	\N
7619204326	-1002304902371	Open Raydium SignalX	rule_1688614	\N
7619204326	-1002370438794	Tiulo Dip Gem	rule_1688614	\N
7619204326	-1001810124798	Maestros Gamble Degen Apes	rule_1688614	\N
7619204326	-1002416522064	Vibrant Raydium SignalX	rule_1688614	\N
8562904531	-1003428380813	Prime Hot VIP .	rule_1336	\N
7619204326	-1001758611100	Gambles 🎲 MadApes	rule_1688614	\N
7065067748	-1001413350311	𝐅𝐫𝐞𝐞 𝐕𝐢𝐏 𝐁𝐨𝐱 🎁	rule_919674	\N
7619204326	-1002380594298	🐋 Free Whale Signals 🐋	rule_1688614	\N
7619204326	-1002478890607	TrendsCoins ™ Solana New Tokens	rule_1688614	\N
7619204326	-1002431017272	0x69420Frank国王	rule_1688614	\N
7619204326	-1001605633079	Wizzy's Casinò	rule_1688614	\N
7619204326	-1002093384030	Solana Early Trending 💵	rule_1688614	\N
7619204326	-1002191114846	🟡 Exclusive Pumpfun Alert	rule_1688614	\N
7619204326	-1002426356770	The Madz Degen	rule_1688614	\N
7619204326	-1002444918055	Ivan shiller 🃏🎴	rule_1688614	\N
7619204326	-1002369628470	Danto Hunter	rule_1688614	\N
7619204326	-1002298132223	Pumpfun Volume Alert 🔥🔥🔥	rule_1688614	\N
5604698232	-1001962346600	91CLUB Game Wingo VIP	rule_35634	\N
5689065087	-1001741296441	91 Club Sure Prediction	rule_536552	\N
6216309591	-1002354214315	The suit analyzer♻️TSA	rule_414976	\N
8213596906	-1001146170349	Binance English	rule_444635	\N
5843862754	-1001129707802	PinkSale (Pink Ecosystem)	rule_451484	\N
6617326165	-1002858860471	DATABASE 2	rule_299365	\N
8260737582	-1001951273532	🫧 Actress World 🌎💙✨🩷😇	rule_1068508	\N
8063683486	-1002665293753	Vip Tricky { Official }	rule_521570	\N
5479267800	-1002689118597	Manyu - $MANYU	rule_528858	\N
7897782049	-1001818778793	Emerge Loads and Lanes!	rule_584660	\N
7098716789	-1002089491508	Loads( Okalar jok)	default	\N
1916333182	-1001381052465	Royal Crypto Boosters	rule_629316	\N
1931035542	-1001469007183	CRYPTO ASTRONAUT	rule_629578	\N
5794338335	-1001488659293	MEXC English (Official)	rule_631776	\N
6876318627	-1001704630087	ULTREOS FOREX SIGNALS 📊️	rule_666944	\N
7337643152	-1002607579978	𝑴𝒐𝒏𝒌𝒆𝒚 𝒄𝒓𝒚𝒑𝒕𝒐 𝒃𝒐𝒙 🎧	rule_779226	\N
1013148420	-1001421302690	𝗡𝗜𝗚𝗛𝗧 𝗠𝗔𝗦𝗧𝗜 🍑	rule_706016	\N
1013148420	-1002468166774	Hot tadka	rule_706016	\N
8358336845	-1002681666814	𝑶𝒑𝒆𝒏 𝑪𝒉𝒂𝒕 𝒘𝒊𝒕𝒉 𝑭𝒓𝒊𝒆𝒏𝒅𝒔🐝	rule_80397	\N
7300111554	-1002406742164	Shopping Deals Loot Deals Offers	rule_216260	\N
7835273890	-1002796219919	Gaming Adda🎯 | Wingo prediction🎰🎴	rule_214257	\N
7786809003	8492857337	atm.day — Stream Scalping Algo	rule_243133	atmstreamalgo_bot
7786809003	8443754133	atm.day — four.meme algo (beta)	rule_243252	atmfourmeme_bot
5451735544	-1003305185549	Penguin fackkky	rule_265425	\N
6159085054	-1001072723547	Cointelegraph	rule_265926	\N
1992060940	-1002858860471	DATABASE 2	rule_302840	\N
7786809003	-5000750408	Test1 atm day	rule_333451	\N
6171495250	-1001670336143	Prasadtechintelugu	rule_343254	\N
7962843287	-1001884352027	𝟓𝟏 𝐆𝐀𝐌𝐄 𝐆𝐈𝐅𝐓 𝐂𝐎𝐃𝐄 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋	rule_358910	\N
7962843287	-1002183179994	ZYAN LOOTER [ Official ]	rule_358910	\N
7962843287	-1001658791554	𝐄𝐋𝐀𝐁𝐎𝐑𝐀𝐓𝐄 𝐄𝐑𝐀	rule_358910	\N
7962843287	-1002136181042	RRR FREE LOOTERS ❤️🛬	rule_358910	\N
7962843287	-1002547936959	𝐋𝐄𝐆𝐄𝐍𝐃 𝐆𝐈𝐅𝐓 𝐂𝐎𝐃𝐄	rule_358910	\N
7962843287	-1001645623802	𝐀𝐋𝐋 𝐏𝐋𝐀𝐓𝐅𝐎𝐑𝐌 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍	rule_358910	\N
7962843287	-1001195609093	𝐄𝐍𝐕𝐄𝐋𝐎𝐏𝐒 𝐇𝐔𝐁	rule_358910	\N
6806206534	-1003348771266	HSC GENIUS HUB	rule_688987	\N
7962843287	-1002047595855	UNLIMITED CODES ❤️❤️❤️❤️	rule_358910	\N
7962843287	-1002005743047	𝐌𝐊 𝐂𝐎𝐃𝐄 𝐋𝐎𝐎𝐓𝐒 ™🚀	rule_358910	\N
7962843287	-1002232583800	TH Code 💸	rule_358910	\N
7635975214	-1003113018838	तुलसी दास मटका	rule_821313	\N
8494703426	-1001820088359	QUOTEX Live SIGNALS 🤖📊	rule_831899	\N
7962843287	-1002403599786	𝗚𝗼𝗮 𝗚𝗮𝗺𝗲𝘀 𝗚𝗶𝗳𝘁 𝗖𝗼𝗱𝗲𝘀	rule_358910	\N
7962843287	-1002340652523	𝘼𝙇𝙁𝘼 𝙀𝘼𝙍𝙉𝙄𝙉𝙂 𝙏𝙍𝙄𝙆𝙎	rule_358910	\N
7962843287	-1001741296441	91 Club Sure Prediction	rule_358910	\N
7844185193	-1003484702452	𝓐𝓛𝓔𝓧 мєтнσd ωσяℓd σтρ gяσυρ	rule_120843	\N
7962843287	-1001990172768	𝟓𝟓 𝐂𝐋𝐔𝐁 𝐕𝐈𝐏 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 🔥	rule_358910	\N
7962843287	-1002178837823	VIP PREDICTION_ IN999	rule_358910	\N
7962843287	-1002006820927	Sigma trick	rule_358910	\N
5090523346	-1002964924744	➢ 𝗙𝘅𝘁 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𓆪 🦅	rule_403738	\N
8594095910	-1001450792566	O'zbekiston 24	rule_36683	\N
8360443949	-1002743050170	♻️ 𝐅𝐢𝐥𝐞 𝐇𝐮𝐛 || 𝐆𝐫𝐚𝐝𝐮𝐚𝐭𝐞 𝐌𝐨𝐯𝐢𝐞𝐬 ♻️	rule_299453	\N
8357880060	-1001469007183	CRYPTO ASTRONAUT	rule_443947	\N
5479267800	-1001129707802	PinkSale (Pink Ecosystem)	default	\N
5907554483	-1001146170349	Binance English	rule_452727	\N
625596166	-1002726550105	Okay Bro	rule_211950	\N
1019557777	-1001954872590	𝐂𝐢𝐧𝐞𝐦𝐚 𝐍𝐚𝐚𝐛	rule_212814	\N
6292741991	-1003637649094	NEWWW	rule_477180	\N
5285734779	-1003657981531	SANTA BNBBBB	rule_477746	\N
1738839153	-1002428240388	FXTV - VIP 2.0 🌴	rule_307630	\N
8566633996	-1003456641241	1% By TCG	rule_189993	\N
535085855	-1003227930803	SignalWale ICT	rule_332600	\N
7452823412	-1001889332976	Cryptobox Parser	rule_680791	\N
6082027138	-1002316045977	Aura Deals & Offers	rule_333452	\N
7047677983	-1003220847604	Manish auto 1	rule_5484	\N
8357312111	-1002186023902	𝗬𝗮𝗱𝗮𝘃 𝗕𝗵𝗮𝗶 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹	rule_6238	\N
8288097205	-1002531749438	Universal cinemas request	rule_42011	\N
8566633996	-1003456641241	1% By TCG	rule_59028	\N
7827652929	-1001389613082	Hotcoin Official	rule_525672	\N
7441972956	-1001469007183	CRYPTO ASTRONAUT	rule_526198	\N
5803322217	-1002520985680	@BASETRENDFUN (LIVE)	rule_526652	\N
5803322217	-1001807989566	@BSCTRENDING (LIVE)	rule_526652	\N
5803322217	-1001443570641	@ETHTRENDING (LIVE)	rule_526652	\N
5803322217	-1002066575222	SOL TRENDING	rule_526652	\N
5803322217	-1001675723936	@buytech Tracker (LIVE)	rule_526652	\N
5803322217	5976408419	D.BuyBot	rule_526652	\N
7829152048	-1001872223162	Bitget English Official	rule_527237	\N
7428775931	-1001573618691	Gate Exchange	rule_527822	\N
5803322217	-1002466039015	Utily Trending 🚀	rule_526652	\N
7098716789	7098716789	Aidarkhan	rule_591291	\N
5920013494	-1003369777573	OracleX English Community	rule_630475	\N
6640526724	-1002431030677	Strike Labs	rule_628749	\N
5747969128	-1001274333834	Coin Mühendisi (Topluluk)	rule_631076	\N
5457458340	-1001431113495	LBank Official Group	rule_631366	\N
8188198606	-1003658844659	4000 data	rule_1691815	\N
8450125934	-1001529005949	💠 𝗛𝗲𝘀𝗯𝘂𝗿𝗴𝗲𝗿 💠 𝗘𝘀𝘁𝗼𝗻𝗶𝗮 🇪🇪	rule_702337	\N
7187275939	-1003680439928	Rzk Tips and tricks	default	\N
6396777448	-1002485854209	Private	default	\N
6396777448	-1002485854209	Private	rule_1173123	\N
6848720005	-1003531079885	INSTA VIRAL VIDEO	rule_38028	\N
6848720005	7247805209	DW2DW_LinkConverterBot	rule_38098	DW2DW_LinkConverterBot
6848720005	-1002995468589	🥵🍑insta viral video 🥵🍑	rule_38176	\N
6848720005	-1003531079885	INSTA VIRAL VIDEO	rule_38176	\N
6848720005	7247805209	DW2DW_LinkConverterBot	rule_38211	DW2DW_LinkConverterBot
8329946072	-1001690616187	All Yono Limited Gifts Code	rule_1249508	\N
6031182200	-1001557671514	XM Trading Academy	rule_1292813	\N
2061093227	-1002449761804	𝗚𝗢𝗟𝗗 𝗣𝗜𝗣𝗦	rule_1306930	\N
7500700453	-1001450792566	O'zbekiston 24	default	\N
7500700453	-1001450792566	O'zbekiston 24	rule_1384049	\N
8000547764	-1002287144768	دوره جدید مصطفی رسولی MR7	rule_1418446	\N
7555800019	-1003551404273	TEAM AZXXY	rule_1809177	\N
7555800019	-1003551404273	TEAM AZXXY	rule_1807764	\N
6848720005	-1002995468589	🥵🍑insta viral video 🥵🍑	rule_1448114	\N
6848720005	-1003182063853	🙈𝗠𝗼𝗺 𝗦𝗼𝗻 𝗱𝘂𝗻𝗶𝘆𝗮🙈	rule_1448114	\N
6848720005	-1003497073753	💥 𝟬𝗬𝟬 𝗛𝗢𝗧𝗘𝗟 𝗩!𝗥𝗔𝗟 🥰	rule_1448114	\N
6848720005	-1003377401410	🥰🤗𝐁𝐡𝐚𝐛𝐡𝐢 𝐥𝐨𝐯𝐞𝐫𝐬🤩😘	rule_1448114	\N
6848720005	-1003081984706	💟 𝐃𝐢𝐬𝐤𝐖𝐚𝐥𝐚 𝐕𝐢𝐝𝐞𝐨 🥶	rule_1448114	\N
6848720005	7247805209	DW2DW_LinkConverterBot	rule_1448198	DW2DW_LinkConverterBot
6848720005	-1001145806748	𝘽𝙝𝙖𝙞 𝙡𝙞𝙣𝙠 𝙡𝙚 💦	rule_1449885	\N
6848720005	-1001101302099	𝗠𝗮𝘀𝗮𝗹𝗮 𝗠𝗮𝘀𝘁𝗶	rule_1449885	\N
6848720005	-1001142177284	🤌🏼 𝙡!𝙣𝙠 𝙬𝙖𝙡𝙖 😋	rule_1449885	\N
6848720005	-1003256075543	Insta Leaked videos	rule_1449885	\N
6848720005	-1003567140776	𝐍𝐞𝐰 𝐇𝐚𝐦𝐬𝐭𝐞𝐫𝐬 🫨	rule_1449885	\N
6848720005	8239533197	@LinkConvertTerabot	rule_1449943	LinkConvertTera2bot
6848720005	-1001145806748	𝘽𝙝𝙖𝙞 𝙡𝙞𝙣𝙠 𝙡𝙚 💦	rule_1450102	\N
6848720005	-1001101302099	𝗠𝗮𝘀𝗮𝗹𝗮 𝗠𝗮𝘀𝘁𝗶	rule_1450102	\N
6848720005	-1001142177284	🤌🏼 𝙡!𝙣𝙠 𝙬𝙖𝙡𝙖 😋	rule_1450102	\N
6848720005	-1003333411893	💯𝐓𝐞𝐫𝐚𝐛𝐨𝐱 𝐕𝐚𝐥𝐢 𝐕𝐢𝐝𝐞𝐨💥	rule_1450102	\N
6848720005	-1003348332198	💘𝐈𝐧𝐬𝐭𝐚𝐠𝐫𝐚𝐦 𝐕𝐢𝐫𝐚𝐥 𝐕𝐢𝐝𝐞𝐨	rule_1450102	\N
6848720005	8382618961	@LinkConvertTerabot	rule_1450181	LinkConvertTeraAbot
6848720005	-1003333411893	💯𝐓𝐞𝐫𝐚𝐛𝐨𝐱 𝐕𝐚𝐥𝐢 𝐕𝐢𝐝𝐞𝐨💥	rule_1450242	\N
6848720005	-1003095471985	🥵𝐕𝐢𝐫𝐚𝐥 𝐋𝐞𝐚𝐤𝐞𝐝 𝐕𝐢𝐝𝐞𝐨𝐬 🥵	rule_1450242	\N
6848720005	-1001389977201	Bang bang	rule_1450242	\N
6848720005	-1003227056319	🥶𝐏𝐫𝐢𝐲𝐚𝐧𝐤𝐚 𝐋𝐢𝐧𝐤𝐬 🥶	rule_1450242	\N
6848720005	-1003440009364	‼️𝑰𝒏𝒔𝒕𝒂𝒈𝒓𝒂𝒎 𝑽𝒊𝒓𝒂𝒍 𝑽𝒊𝒅𝒆𝒐🚨	rule_1450242	\N
6848720005	8236128760	@LinkConvertTerabot	rule_1450317	LinkConvertTera3bot
7353874683	-1002240834471	𝘽𝙪𝙇𝙇𝙈𝙤𝙫𝙞𝙚𝙨 ™	rule_842862	\N
7885730692	-1001289454424	Sharemarket Information️	rule_1521283	\N
6942557751	-1003112109919	Thor database channel 🎬	rule_128212	\N
7885730692	-1001202426378	STOCK MARKET NEWS UPDATE	rule_1521283	\N
5662756526	-1003415304145	Garant Savdo | #UZG	rule_1560286	\N
6331543504	-1002720543880	Ipl fan	rule_1334118	\N
\.


--
-- Data for Name: subscription_notifications; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.subscription_notifications (user_id, last_expiry_notification, notified_for_plan) FROM stdin;
7452823412	2025-10-24 15:51:35.934928	limit_enforcement
5989213998	2025-11-08 16:05:25.034688	expiring_1month
7162132327	2025-12-11 22:11:58.493602	limit_enforcement
7714089439	2025-11-09 11:07:05.203289	limit_enforcement
5081757613	2025-10-26 21:15:46.686991	limit_enforcement
8258901462	2025-10-26 21:15:58.041936	limit_enforcement
5891568590	2025-12-09 18:28:02.426556	expired_1month
8083890417	2025-11-19 14:27:54.02571	limit_enforcement
5406442663	2025-11-19 14:27:54.398314	limit_enforcement
6434063803	2025-11-19 14:27:54.936088	limit_enforcement
7786809003	2025-11-19 14:27:55.437207	limit_enforcement
8224373261	2025-11-19 14:27:55.803138	limit_enforcement
7337643152	2025-11-19 14:27:56.240656	limit_enforcement
1327566897	2025-11-19 14:27:56.640217	limit_enforcement
8126606818	2025-11-19 14:27:57.159447	limit_enforcement
7555800019	2025-12-22 09:04:35.978685	expiring_1month
906648890	2026-01-04 19:33:35.16881	limit_enforcement
8566633996	2026-01-04 23:36:16.875743	expiring_1month
7885730692	2025-12-29 21:37:39.143562	expiring_1month
7903348966	2025-12-25 07:44:35.761637	expired_1month
6112363781	2026-01-05 08:27:59.840252	expiring_1month
6331543504	2026-01-02 15:19:51.178644	expiring_1month
7619204326	2025-12-30 06:53:56.80446	expired_1month
7962843287	2026-01-05 09:38:55.472923	expired_1month
1444313827	2026-01-05 11:10:04.514881	expired_1month
7301764474	2026-01-05 11:10:04.528956	expired_1month
1992060940	2026-01-05 11:50:34.843629	expired_1month
7488003312	2026-01-02 18:21:55.269903	expired_1month
7669122337	2026-01-05 11:50:34.858971	expired_1month
5663097688	2026-01-05 12:36:08.505255	expired_1month
6532735248	2026-01-05 12:41:12.04866	expired_1month
8370995918	2025-12-27 00:23:06.30703	expired_1month
6848720005	2025-12-25 20:26:47.717123	expired_1month
6421644491	2025-12-29 09:38:15.132328	expired_1month
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.subscriptions (user_id, plan, expires_at, purchased_at, notified_about_expiry, notified_about_expiry_soon) FROM stdin;
1013148420	1year	2053-02-13 15:08:53.606257	2025-09-28 15:08:53.607124	f	f
8127965483	3months	2026-01-21 12:01:19.601469	2025-10-23 12:01:19.602439	f	f
5891568590	1month	2025-11-09 18:50:00.416646	2025-10-10 18:50:00.417578	t	t
5989213998	1month	2025-11-11 16:02:01.8662	2025-10-12 16:02:01.866959	t	t
6082027138	3months	2026-02-15 22:32:12.762735	2025-11-17 22:32:12.763557	f	f
7903348966	1month	2025-11-25 08:44:17.954178	2025-10-26 08:44:17.955622	t	t
8370995918	1month	2025-11-27 02:49:11.969161	2025-10-28 02:49:11.970135	t	t
7488003312	1month	2025-12-03 22:09:18.537333	2025-11-03 22:09:18.538089	t	t
1019557777	1month	2026-01-08 21:11:29.499303	2025-12-09 21:11:29.500038	f	f
7669122337	1month	2025-12-13 07:31:52.262932	2025-11-13 07:31:52.263766	t	t
7786809003	1month	2026-01-13 14:33:33.660201	2025-12-14 14:33:33.661359	f	f
6159085054	1month	2026-01-14 08:09:56.851379	2025-12-15 08:09:56.852346	f	f
7238808048	1month	2026-01-14 19:16:24.266226	2025-12-15 19:16:24.267408	f	f
6532735248	1month	2025-12-17 14:35:55.691319	2025-11-17 14:35:55.692626	t	t
5803322217	1month	2026-01-16 23:25:33.202696	2025-12-17 23:25:33.204183	f	f
7962843287	1month	2025-12-21 20:49:09.632002	2025-11-21 20:49:09.63288	t	t
7301764474	1month	2025-12-24 15:17:19.132616	2025-11-24 15:17:19.133375	t	t
7555800019	1month	2026-01-24 08:36:42.548976	2025-12-25 08:36:42.54988	f	f
6848720005	1month	2026-01-24 21:46:25.118253	2025-12-25 21:46:25.119165	f	f
1444313827	1month	2025-12-26 12:03:04.308316	2025-11-26 12:03:04.309346	t	t
8252877204	1month	2026-01-28 08:20:51.931323	2025-12-29 08:20:51.968645	f	f
6421644491	1month	2026-01-28 12:32:42.465352	2025-12-29 12:32:42.466395	f	f
7619204326	6months	2026-06-28 08:10:28.077472	2025-12-30 08:10:28.078283	f	f
1992060940	1month	2025-12-30 19:00:26.697689	2025-11-30 19:00:26.698595	t	t
7885730692	1month	2026-01-31 12:28:52.426099	2026-01-01 12:28:52.427335	f	f
6331543504	1month	2026-02-01 21:10:56.302894	2026-01-02 21:10:56.303608	f	f
7967694019	1month	2026-02-02 19:40:58.33138	2026-01-03 19:40:58.3328	f	f
8566633996	1month	2026-01-07 23:35:58.939991	2025-12-08 23:35:58.940769	f	t
6112363781	1month	2026-01-08 08:26:43.847828	2025-12-09 08:26:43.848605	f	t
5663097688	1month	2026-01-05 08:25:51.624833	2025-12-06 08:25:51.625683	t	t
\.


--
-- Data for Name: user_activity; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.user_activity (user_id, last_activity, command_count, first_seen) FROM stdin;
8282805291	2025-10-07 19:50:16.465371	8	2025-10-07 19:42:36.653355
6260689203	2025-10-07 01:14:52.832969	2	2025-10-07 01:14:45.413555
8224373261	2025-10-17 22:11:18.58935	18	2025-10-16 11:09:49.737346
7849204364	2025-10-07 06:22:34.525562	5	2025-10-07 06:13:57.075595
1327566897	2025-10-06 11:22:21.577209	7	2025-10-06 07:39:25.173938
5637957213	2025-10-04 18:15:29.548084	2	2025-10-04 18:15:23.567948
5365768574	2025-11-15 23:35:53.639379	14	2025-10-08 20:33:09.713226
1429618267	2025-10-12 15:14:23.222486	4	2025-10-12 15:08:45.486781
1102099467	2025-10-22 13:15:00.808078	2	2025-10-22 13:14:46.752652
6434063803	2025-10-01 13:21:58.70769	18	2025-10-01 12:58:08.982816
7941190412	2025-10-04 19:38:03.511066	6	2025-10-04 19:30:53.513703
8343538070	2025-10-14 07:46:58.207934	7	2025-10-14 07:43:20.51362
5277032865	2025-09-30 16:57:31.286908	13	2025-09-30 16:41:29.746197
7946534196	2025-10-10 07:54:52.523761	8	2025-10-10 07:46:19.126684
7337643152	2025-12-20 22:42:07.376414	31	2025-10-03 22:07:21.533224
8258901462	2025-12-07 02:51:41.053232	36	2025-10-13 14:13:16.057324
5649648021	2025-10-03 17:12:29.768689	1	2025-10-03 17:12:29.768689
7558043394	2025-10-15 20:39:58.993645	8	2025-10-15 20:26:24.35589
7079411596	2025-10-01 23:53:37.175056	6	2025-09-30 16:54:54.546775
7780256505	2025-10-02 00:01:58.297164	2	2025-10-01 23:52:40.599043
6841711384	2025-10-16 08:34:26.879694	1	2025-10-16 08:34:26.879694
8496033325	2025-10-02 23:16:28.834427	1	2025-10-02 23:16:28.834427
6961824287	2025-10-03 00:51:59.243267	3	2025-10-03 00:51:21.777127
6737180183	2025-10-03 07:52:53.376746	2	2025-10-03 07:52:35.025357
2038045502	2025-11-12 20:18:16.475372	15	2025-10-07 17:13:04.505074
6548239090	2025-10-04 01:16:31.356901	2	2025-10-04 01:16:03.856755
6227448330	2025-10-22 21:39:45.714239	2	2025-10-22 21:38:59.886932
6594077403	2025-09-30 21:34:02.126758	5	2025-09-30 21:31:48.830956
5406442663	2025-12-16 05:10:41.732638	42	2025-10-16 03:38:23.028997
6059788941	2025-10-13 21:21:33.324088	8	2025-10-13 21:08:34.316446
8242716115	2025-10-19 10:21:27.341905	3	2025-10-19 10:19:58.071212
8495094059	2025-10-04 20:25:59.707482	7	2025-10-04 20:17:24.524362
7864970371	2025-10-19 16:01:22.996456	2	2025-10-19 16:01:21.318718
7461707862	2025-10-12 02:05:21.847513	2	2025-10-12 02:05:04.194451
1020100092	2025-10-03 10:30:07.178054	17	2025-10-03 10:11:11.979482
7998925104	2025-10-04 20:50:39.430937	2	2025-10-04 20:47:24.930308
8215282057	2025-10-07 09:03:00.771922	6	2025-10-07 09:00:42.186337
1604618552	2025-10-26 17:26:12.32657	8	2025-10-03 13:56:31.001626
5773544941	2025-10-04 15:13:27.351569	38	2025-10-03 19:09:03.554027
8295741675	2025-10-13 04:17:04.237111	1	2025-10-13 04:17:04.237111
8127965483	2025-10-30 19:45:06.577479	55	2025-10-03 16:40:38.487957
6236247698	2025-10-06 16:41:06.126167	3	2025-10-06 16:39:30.364118
5921486522	2025-10-30 15:40:12.422697	22	2025-10-25 01:26:44.47316
7096845088	2025-11-13 02:47:45.475969	8	2025-09-30 21:37:45.329894
7123794523	2025-11-10 21:00:17.691986	12	2025-10-01 13:28:30.562735
7802521511	2025-10-09 09:35:18.346163	3	2025-10-09 09:34:33.86002
7404167930	2025-10-12 21:12:44.750931	18	2025-10-03 22:11:56.318612
7169845402	2025-10-19 10:24:07.982133	6	2025-10-19 08:28:46.749743
6251096236	2025-10-07 22:22:13.719031	3	2025-10-07 22:21:26.130772
8082996556	2025-10-07 23:48:33.515131	1	2025-10-07 23:48:33.515131
7714089439	2025-11-09 15:08:46.602704	34	2025-09-30 19:48:45.626544
1089312108	2025-10-08 03:52:57.762175	2	2025-10-08 03:52:04.400666
5841727126	2025-10-11 15:59:05.273388	2	2025-10-11 15:58:41.843767
5387866919	2025-10-29 17:18:44.731932	14	2025-10-15 05:01:17.374741
1985298767	2025-10-08 20:36:23.960029	3	2025-10-08 20:34:45.700268
5962804694	2025-10-06 09:16:32.219857	6	2025-10-06 09:11:49.752591
7669122337	2025-11-19 11:42:20.773391	44	2025-10-19 20:41:10.654219
742895166	2025-11-11 22:39:34.691322	71	2025-10-07 14:16:35.720241
6490654709	2025-12-11 07:40:22.030284	67	2025-10-20 17:29:26.006227
6495976374	2025-10-13 19:47:32.789621	3	2025-10-13 19:44:44.178972
725879091	2025-10-22 22:31:05.732692	2	2025-10-22 22:30:43.20222
8266767371	2025-10-09 23:34:00.311244	2	2025-10-09 23:33:47.462141
5902304687	2025-10-15 23:14:47.252465	3	2025-10-15 23:12:17.052538
6806787718	2025-10-08 12:33:59.959805	13	2025-10-08 12:16:06.729956
8447972448	2025-10-14 19:33:23.272846	3	2025-10-14 19:32:02.134583
7611856186	2025-10-10 17:59:57.044317	56	2025-10-04 16:53:07.008525
7695786518	2025-10-16 22:27:26.708361	2	2025-10-16 22:27:15.348384
1637144293	2025-10-15 12:52:10.45989	8	2025-10-15 08:03:04.203035
7144330602	2025-10-11 03:16:00.706457	6	2025-10-11 03:12:25.732137
6654944138	2025-10-09 13:09:53.792102	12	2025-10-09 12:56:49.15782
715041960	2025-10-17 03:39:30.093388	2	2025-10-17 03:39:12.443874
6477484866	2025-10-17 14:38:51.31622	9	2025-10-17 14:29:58.439663
5023503076	2025-10-21 21:39:36.227862	7	2025-10-21 21:30:10.145398
6532735248	2025-12-05 21:08:45.406153	517	2025-10-06 10:49:43.849925
772971972	2025-10-17 06:13:41.968137	1	2025-10-17 06:13:41.968137
6799961892	2025-10-11 17:14:24.706141	5	2025-10-11 17:11:39.816914
8190106961	2025-10-21 14:46:49.098564	5	2025-10-21 14:43:51.889099
5989213998	2025-10-12 17:57:21.531951	19	2025-10-12 15:52:49.440878
7904032877	2025-10-10 20:53:58.492522	3	2025-10-10 20:53:35.561622
8392479231	2025-10-10 20:54:27.606119	1	2025-10-10 20:54:27.606119
8328212126	2025-10-10 05:57:46.444517	7	2025-10-10 05:53:57.059327
8475941468	2025-10-10 20:54:45.658522	2	2025-10-10 20:54:41.426287
5705159607	2025-10-11 14:05:01.490451	1	2025-10-11 14:05:01.490451
6222156706	2025-10-13 12:45:56.207076	26	2025-10-04 17:06:28.777694
7693090424	2025-10-12 12:15:20.333488	15	2025-10-11 17:03:47.594509
7154763189	2025-10-13 20:38:15.625473	50	2025-10-08 16:51:53.311894
7864741147	2025-10-13 14:10:31.593584	2	2025-10-13 14:04:21.893894
5750203191	2025-10-24 17:53:46.672416	4	2025-10-24 17:50:36.283155
6443005862	2025-10-14 20:43:39.21006	1	2025-10-14 20:43:39.21006
1050839502	2025-10-21 10:37:09.969744	6	2025-10-21 05:59:07.761319
8127040286	2025-10-16 01:13:02.256196	11	2025-10-16 01:03:11.236246
7207397625	2025-10-20 09:23:39.187051	3	2025-10-20 09:22:36.193114
5151022617	2025-10-19 08:07:13.035806	5	2025-10-19 08:04:24.423545
8006768154	2025-10-16 09:27:55.842358	29	2025-10-16 08:32:58.707432
7708374058	2025-10-19 12:16:56.049527	3	2025-10-19 12:12:15.223109
7042545583	2025-10-19 18:20:26.001203	7	2025-10-19 18:17:29.766812
7251995251	2025-11-02 17:40:39.010837	46	2025-10-07 14:39:07.66435
5526558073	2025-10-24 21:58:03.574809	12	2025-10-24 21:44:34.874785
7786809003	2025-12-21 20:54:17.122934	186	2025-10-19 16:31:51.114689
762265169	2025-10-22 14:47:02.137896	18	2025-10-17 14:03:05.607085
8195721116	2025-10-19 16:00:36.94017	1	2025-10-19 16:00:36.94017
6449216367	2025-10-20 15:47:29.247886	5	2025-10-20 15:37:45.711194
5891568590	2025-10-26 18:57:55.658044	255	2025-10-09 17:01:07.219478
5769636640	2025-10-21 13:33:54.580707	1	2025-10-21 13:33:54.580707
838299478	2025-10-23 22:16:34.932157	2	2025-10-23 22:16:15.41
7488003312	2025-12-04 21:57:19.15293	233	2025-10-21 13:23:05.755387
8000635184	2025-10-22 10:20:21.718325	9	2025-10-22 10:07:59.834024
6214254455	2025-10-22 21:47:40.328116	3	2025-10-22 21:45:27.098723
6651813666	2025-10-24 14:25:33.17239	37	2025-10-11 19:36:55.68386
8126606818	2025-10-22 23:36:38.307489	15	2025-10-22 23:21:53.422623
8012257232	2025-10-23 17:01:27.686622	5	2025-10-23 16:58:04.249418
7693672756	2025-10-28 17:58:19.869272	9	2025-10-25 00:14:45.285675
7130291737	2025-11-17 16:56:59.283312	15	2025-10-24 01:39:40.451485
7884212451	2025-10-25 14:25:03.549517	6	2025-10-25 13:42:38.536875
6529663543	2025-10-25 14:20:13.61049	17	2025-10-25 13:46:23.095421
5821665830	2025-10-24 22:09:51.920429	7	2025-10-24 22:05:43.659831
7065067748	2025-11-20 22:19:00.261596	85	2025-10-07 21:09:45.459806
6636475980	2025-10-25 12:51:58.251027	13	2025-10-25 12:28:18.36329
6171495250	2025-12-15 21:24:34.131737	29	2025-10-12 16:02:51.497615
7452823412	2025-12-18 12:49:08.092543	91	2025-10-13 21:08:53.363395
7162132327	2025-12-12 01:31:01.036633	7	2025-09-30 11:05:14.027002
945852382	2025-10-25 15:14:27.418319	2	2025-10-25 15:13:51.890105
1052855789	2025-11-02 00:49:36.710522	3	2025-11-02 00:49:09.026085
1815911593	2025-10-25 20:07:37.683775	3	2025-10-25 20:07:01.779825
5709280385	2025-10-26 03:02:17.534296	2	2025-10-26 03:02:04.899562
6197651571	2025-10-26 03:03:18.661539	2	2025-10-26 03:03:16.371423
5420999986	2025-12-08 14:14:37.950786	10	2025-11-09 10:43:43.608002
7497167766	2025-11-05 20:21:54.852928	3	2025-11-05 20:21:33.266873
969099516	2025-11-03 05:30:28.972036	12	2025-11-03 05:10:48.007534
829793383	2025-10-30 09:54:50.497683	2	2025-10-30 09:54:41.357275
6331543504	2026-01-04 14:40:07.886665	161	2025-09-28 17:07:15.418953
5081757613	2026-01-05 00:57:15.538784	11	2025-10-01 11:04:59.068316
6421644491	2026-01-04 11:08:16.608203	682	2025-10-17 10:22:53.186031
6087538623	2026-01-02 21:40:57.611	180	2025-10-09 18:17:45.843226
1187626542	2025-10-30 11:54:47.942687	2	2025-10-30 11:54:44.638186
8366317825	2025-11-03 05:34:20.021062	3	2025-11-03 05:34:19.484873
276419595	2025-10-30 12:20:41.401954	2	2025-10-30 12:20:36.610499
8370995918	2025-10-28 00:05:39.202002	15	2025-10-27 23:50:50.153066
6526942062	2025-11-13 15:19:56.719912	9	2025-11-13 15:13:25.84759
7430101095	2025-11-12 02:24:44.749612	11	2025-11-12 02:17:56.406509
7174833388	2025-11-05 10:31:39.902303	10	2025-11-05 10:24:26.636393
7752022043	2025-11-18 08:51:16.113893	12	2025-11-12 16:22:37.116731
723189008	2025-11-03 09:23:58.507098	7	2025-11-03 08:29:55.984251
8140482478	2025-10-30 16:43:31.717665	12	2025-10-30 16:32:25.013069
8363119814	2025-10-26 11:21:38.619445	1	2025-10-26 11:21:38.619445
6959900911	2025-10-30 22:34:20.851792	1	2025-10-30 22:34:20.851792
7903348966	2025-10-26 12:15:27.66263	30	2025-10-26 03:23:02.693885
6521962854	2025-11-02 01:32:46.320322	5	2025-11-02 01:31:51.589731
6830041427	2025-11-03 10:50:54.126372	38	2025-10-31 16:52:41.034163
7424149568	2025-10-26 19:34:15.438574	3	2025-10-26 19:31:47.933502
5848770400	2025-10-28 18:23:24.442535	5	2025-10-28 18:13:51.367231
8281707866	2025-11-22 11:07:54.329202	62	2025-10-30 22:35:31.837491
5260143179	2025-10-28 21:21:41.670056	1	2025-10-28 21:21:41.670056
7433900109	2025-10-27 10:48:05.969068	6	2025-10-27 10:43:04.2579
6305231297	2025-11-07 19:04:27.390939	9	2025-11-07 18:57:08.571155
1793299869	2025-11-03 12:19:14.943496	1	2025-11-03 12:19:14.943496
7796576246	2025-11-02 02:05:32.241366	7	2025-11-02 02:00:10.95168
417068575	2025-10-28 21:54:03.791998	6	2025-10-28 21:47:13.105251
5473589003	2025-11-02 14:07:34.517056	4	2025-11-02 14:06:41.184269
6174856335	2025-11-05 10:36:16.411136	11	2025-11-05 10:29:57.190669
5451780987	2025-11-03 18:07:31.1145	5	2025-11-03 08:50:57.568306
6390957187	2025-10-31 20:03:13.696311	1	2025-10-31 20:03:13.696311
8323818787	2025-10-27 12:47:32.025946	4	2025-10-27 12:41:11.250317
8069225688	2025-11-02 16:26:54.219084	7	2025-11-02 16:22:46.331195
5748157494	2025-10-27 13:43:46.39593	4	2025-10-27 13:41:38.682683
6548104664	2025-11-05 12:28:04.218387	3	2025-11-05 12:27:25.223328
7582960557	2025-11-02 16:27:49.042143	3	2025-11-02 16:27:46.222283
1700711970	2025-11-04 08:56:26.431528	5	2025-11-04 08:54:24.319996
7488381628	2025-10-31 20:27:03.789848	9	2025-10-31 20:10:01.837767
7559151456	2025-10-27 18:27:48.951006	5	2025-10-27 18:24:06.290401
8296721301	2025-10-31 01:37:18.118215	9	2025-10-31 01:06:38.285943
8293930284	2025-11-05 20:50:28.774875	9	2025-11-05 20:47:01.753842
8258364810	2025-10-31 01:49:40.663869	3	2025-10-31 01:49:05.351697
6548675223	2025-10-31 21:59:06.02069	3	2025-10-31 21:58:51.998359
1212321102	2025-11-04 09:21:03.415933	3	2025-11-04 09:21:00.273436
727207241	2025-11-04 10:06:28.440569	1	2025-11-04 10:06:28.440569
8460919996	2025-10-31 01:52:48.144936	5	2025-10-31 01:50:05.039086
2012655294	2025-11-06 19:34:19.783894	30	2025-11-06 12:54:40.482446
6729148139	2025-10-29 16:39:57.663023	3	2025-10-29 16:38:17.310885
7096763267	2025-11-02 20:46:02.093267	7	2025-11-02 20:35:54.031067
7258034641	2025-11-02 20:48:05.241835	3	2025-11-02 20:48:00.342049
7209556360	2025-10-31 02:05:56.098635	11	2025-10-31 01:52:02.436099
5554471923	2025-11-04 16:08:20.095075	6	2025-11-04 15:49:27.61593
7638667601	2025-10-31 02:06:48.451702	5	2025-10-31 02:00:42.119942
1080335438	2025-10-31 09:37:33.104638	3	2025-10-31 09:37:18.026684
1165817080	2025-11-04 23:31:28.694986	3	2025-11-04 23:31:24.511285
1986648923	2025-11-06 21:11:53.34286	3	2025-11-06 21:10:22.29899
1837260280	2025-11-02 20:59:36.35653	8	2025-11-02 20:56:41.812357
5779210849	2025-11-01 14:48:18.003776	8	2025-11-01 14:39:48.781387
6636522096	2025-10-31 15:40:55.262767	11	2025-10-31 11:22:48.748558
5586537077	2025-10-31 16:52:29.847289	3	2025-10-31 16:51:03.572813
1740299437	2025-11-08 02:34:53.807196	3	2025-11-08 02:34:41.574065
1273075258	2025-11-05 00:43:22.938735	5	2025-11-05 00:38:22.502413
7431619619	2025-11-01 19:19:11.683699	5	2025-11-01 19:10:29.233752
5332226638	2025-11-02 23:14:03.760441	5	2025-11-02 23:09:37.419302
1932336561	2025-11-01 20:30:22.298772	5	2025-11-01 20:29:11.885718
6109005671	2025-11-06 15:48:26.37329	7	2025-11-06 15:46:39.204977
987307481	2025-11-01 21:34:04.166405	1	2025-11-01 21:34:04.166405
8280548411	2025-11-05 13:00:47.350537	12	2025-11-05 12:40:03.874895
6910150860	2025-11-11 10:35:07.082957	27	2025-11-11 10:01:06.357213
1606109505	2025-11-05 17:26:52.737617	3	2025-11-05 17:26:49.478623
268398314	2025-11-09 09:47:42.328154	3	2025-11-09 09:47:03.801176
5445448223	2025-11-07 01:30:47.655221	15	2025-11-06 15:58:00.78858
314357706	2025-11-05 19:34:28.678062	1	2025-11-05 19:34:28.678062
640552862	2025-11-09 10:28:20.075081	1	2025-11-09 10:28:20.075081
6027932766	2025-11-05 00:58:47.31861	15	2025-11-05 00:43:45.386279
6588828344	2025-11-05 22:17:35.354861	17	2025-11-05 19:36:25.337677
5389796957	2025-12-11 12:13:21.615681	6	2025-11-01 21:24:44.670689
6643950757	2025-11-09 13:18:26.203267	1	2025-11-09 13:18:26.203267
224436552	2025-11-08 09:16:24.522965	9	2025-11-08 09:06:18.39277
5111664320	2025-11-06 15:54:59.094939	13	2025-11-06 15:44:01.949008
1454823971	2025-11-05 20:17:51.352809	3	2025-11-05 20:16:53.220602
1143477549	2025-11-05 20:17:51.679785	1	2025-11-05 20:17:51.679785
1608543480	2025-11-10 21:19:41.885923	10	2025-11-10 21:02:21.49786
8096483755	2025-11-09 21:24:06.077956	5	2025-11-09 21:21:33.306529
6779399346	2025-11-10 16:14:44.296326	8	2025-11-10 16:09:46.577975
6876778776	2025-11-13 03:27:40.674224	5	2025-11-13 03:21:24.829865
7319777571	2025-11-07 09:13:24.489183	15	2025-11-06 16:27:00.395432
7630870798	2025-11-13 07:11:29.685018	1	2025-11-13 07:11:29.685018
649455144	2025-11-10 23:05:35.560493	4	2025-11-10 23:02:20.262705
6852552336	2025-11-19 23:57:57.097944	9	2025-11-10 16:02:52.222102
7880089937	2025-11-12 07:30:05.310109	5	2025-11-12 07:28:05.087544
6450202144	2025-11-14 15:09:19.111551	15	2025-11-14 15:04:41.170901
5223712026	2025-11-12 09:30:37.355793	3	2025-11-12 09:30:28.659607
6078490717	2025-11-10 18:21:22.729167	15	2025-11-10 14:27:40.661269
7224107415	2025-11-14 07:54:23.182487	12	2025-11-14 07:50:53.55805
7793805367	2025-11-11 05:54:00.687726	1	2025-11-11 05:54:00.687726
-1003186362121	2025-11-18 10:40:29.65565	3	2025-11-01 19:49:43.436459
1655661346	2025-11-16 14:19:59.877805	16	2025-11-16 14:08:15.078418
5964390462	2025-11-12 19:38:36.888824	10	2025-11-12 02:17:24.883145
6006765394	2025-11-14 17:15:51.297275	1	2025-11-14 17:15:51.297275
8382351343	2025-11-15 03:08:32.592022	3	2025-11-15 03:05:27.369085
7811318319	2025-11-15 19:10:12.007571	5	2025-11-15 19:08:21.578536
6366929184	2025-11-14 17:33:25.005287	10	2025-11-14 15:58:48.519776
8006993274	2025-11-15 11:23:46.503902	23	2025-11-15 11:07:50.454969
6401097967	2025-11-15 13:30:27.751002	1	2025-11-15 13:30:27.751002
5048374807	2025-11-16 14:44:10.485405	8	2025-11-16 14:36:38.327546
8260737582	2025-11-16 16:53:02.749916	8	2025-11-16 16:49:01.465528
7544899269	2025-11-16 16:48:25.22841	3	2025-11-16 16:47:35.322502
7803536162	2025-11-16 20:01:14.211683	8	2025-11-16 19:57:52.897243
5090851627	2025-11-17 00:08:40.795574	3	2025-11-17 00:08:22.762644
1847314431	2025-11-17 03:11:54.991873	3	2025-11-17 03:11:37.695328
644025134	2025-11-17 16:08:19.074452	7	2025-11-17 16:00:26.038634
6673145441	2025-11-17 17:16:00.434073	3	2025-11-17 17:15:48.336659
6570157953	2025-11-17 19:46:28.253547	5	2025-11-17 19:00:23.695011
6551218990	2025-11-18 17:36:29.565316	18	2025-11-17 17:16:16.569399
5663097688	2025-12-06 07:18:16.891304	37	2025-11-06 16:16:48.340656
404962727	2025-12-14 23:48:13.853925	11	2025-12-14 23:41:28.241856
6019705184	2025-11-17 22:48:02.081242	3	2025-11-17 22:47:46.084356
8420999594	2025-12-12 20:15:53.726285	3	2025-12-12 20:14:22.810401
1842957283	2025-11-19 15:22:01.59831	3	2025-11-19 15:21:53.511687
8243850085	2025-11-19 15:22:23.7292	3	2025-11-19 15:22:17.653963
6373849461	2025-11-21 21:27:00.600699	3	2025-11-21 21:26:14.676935
1203102788	2025-11-25 19:37:42.855468	5	2025-11-25 19:34:37.904607
6514739688	2025-11-28 07:37:51.246986	6	2025-11-28 07:35:00.189509
7851938753	2025-12-07 16:54:54.456672	7	2025-12-07 16:53:58.082639
7441972956	2025-12-18 00:28:47.065916	16	2025-12-17 04:05:55.611725
8106692932	2025-11-25 20:43:04.792081	14	2025-11-25 17:33:29.122348
1026086849	2025-11-26 02:15:06.447981	13	2025-11-25 12:49:25.100512
7246249229	2025-12-01 20:49:22.601191	4	2025-12-01 20:48:09.240919
7347667622	2025-12-03 16:51:25.393247	7	2025-12-03 16:45:26.187218
1219098432	2025-11-22 17:57:45.990937	3	2025-11-22 17:52:09.312128
5188094832	2025-11-19 20:31:22.930941	3	2025-11-19 20:27:16.774072
5877679060	2025-12-08 22:22:43.706642	5	2025-12-08 22:21:23.088669
1444313827	2025-12-26 02:39:02.395145	30	2025-11-14 00:24:42.251392
6082027138	2025-12-27 14:32:33.778233	51	2025-11-17 22:22:44.795761
7619204326	2026-01-02 05:15:48.021582	275	2025-10-26 18:42:28.661299
7885730692	2026-01-01 13:48:22.807245	60	2025-11-05 17:28:03.69194
8373606719	2025-12-11 09:47:06.591023	7	2025-12-11 09:40:22.072976
6818938551	2025-12-01 20:52:26.431823	12	2025-12-01 20:46:28.658085
7849292154	2025-12-15 15:46:38.676928	3	2025-12-15 15:46:25.523912
1249672673	2025-12-02 08:12:19.351858	3	2025-12-02 08:12:15.739818
8276262057	2025-11-23 21:59:04.428471	7	2025-11-23 21:52:48.423446
5445031425	2025-11-19 21:17:47.482329	19	2025-11-19 20:49:47.340572
7651601632	2025-11-23 09:52:18.650704	5	2025-11-23 09:50:16.590624
7420928487	2025-11-20 08:53:42.050203	3	2025-11-20 08:53:16.061014
6271999767	2025-11-26 08:07:55.303682	16	2025-11-26 08:01:51.595288
8376367600	2025-12-10 10:17:39.674817	1	2025-12-10 10:17:39.674817
1645739978	2025-11-24 19:59:50.484443	5	2025-11-24 19:57:49.596747
8592109876	2025-11-26 11:30:44.352036	3	2025-11-26 11:30:19.925306
6275898399	2025-12-10 10:46:43.511928	1	2025-12-10 10:46:43.511928
7841164931	2025-12-11 12:39:21.102535	4	2025-12-11 12:31:12.460604
6306052652	2025-12-02 08:17:44.628259	6	2025-12-02 08:12:53.688136
8431307336	2025-12-07 21:13:27.644008	20	2025-11-29 14:17:20.477987
6731196663	2025-11-20 18:45:06.14279	13	2025-11-20 18:37:51.300233
8197283750	2025-11-26 23:56:36.35847	1	2025-11-26 23:56:36.35847
8562904531	2025-11-27 01:30:10.613476	8	2025-11-26 22:43:57.517816
8023791486	2025-11-25 00:42:34.133245	5	2025-11-25 00:39:51.115364
105491939	2025-12-04 08:24:07.899521	3	2025-12-04 08:23:58.544503
6981030493	2025-11-21 15:18:03.441373	14	2025-11-20 13:08:05.958194
5799045869	2025-11-25 01:04:30.496213	3	2025-11-25 01:04:28.304399
7047677983	2025-12-11 23:37:18.088598	12	2025-12-11 23:29:27.341708
7561334327	2025-11-21 16:30:14.598195	7	2025-11-21 16:26:28.950985
6627996847	2025-11-28 19:42:07.628208	1	2025-11-28 19:42:07.628208
6013957379	2025-12-02 17:27:19.207307	10	2025-12-02 17:21:09.012462
1816095222	2025-12-07 21:47:15.395342	3	2025-12-07 21:46:56.418117
7202193085	2025-12-04 10:30:38.16336	5	2025-12-04 10:23:17.751686
7636116711	2025-11-21 16:49:15.612531	8	2025-11-21 16:46:30.462761
5970515469	2025-11-28 22:32:31.218221	5	2025-11-28 22:30:43.430294
7967992181	2025-12-08 02:21:50.202053	2	2025-12-08 02:21:28.895683
6889190828	2025-12-04 13:01:27.57723	3	2025-12-04 12:32:13.176301
7835273890	2025-12-14 20:09:59.246484	15	2025-12-14 09:30:14.290278
636735577	2025-12-08 10:19:48.691177	21	2025-12-04 06:19:23.893455
1597547826	2025-11-29 14:16:09.037564	3	2025-11-29 14:16:04.130662
7481655751	2025-12-09 17:15:17.585406	5	2025-12-09 17:14:05.8692
5057018016	2025-12-08 16:43:17.457358	3	2025-12-08 16:43:08.08477
7866745942	2025-11-25 10:27:53.661807	9	2025-11-25 10:22:53.797627
1414116736	2025-12-01 00:16:42.288602	15	2025-12-01 00:00:36.800247
7895417063	2025-12-01 00:32:03.034437	1	2025-12-01 00:32:03.034437
6514184808	2025-12-03 03:50:08.994197	5	2025-12-03 03:47:13.532014
8291148450	2025-12-14 00:36:20.142458	12	2025-12-14 00:31:51.104535
7288654716	2025-12-04 18:30:43.128855	1	2025-12-04 18:30:43.128855
1549571710	2025-11-27 22:36:23.446149	10	2025-11-27 21:41:21.582364
8113465727	2025-12-03 09:53:23.938892	5	2025-12-03 09:51:28.86486
7635975214	2025-12-06 11:55:49.22347	15	2025-12-06 11:48:18.861813
1113471444	2025-12-01 02:50:11.080429	12	2025-12-01 02:14:16.076276
6520648636	2025-11-29 23:27:26.532784	7	2025-11-29 23:21:09.35847
8357312111	2025-12-11 23:46:22.836539	6	2025-12-11 23:41:13.294379
843361843	2025-12-06 12:01:36.290487	3	2025-12-06 11:59:23.433552
6806206534	2025-12-04 23:06:56.996088	5	2025-12-04 23:02:11.059562
7533748651	2025-11-28 07:33:39.908529	3	2025-11-28 07:32:56.095475
530131604	2025-12-03 16:02:21.177649	11	2025-12-03 15:46:54.27942
8040370079	2025-12-01 20:43:37.084123	10	2025-12-01 20:23:30.372283
8594095910	2025-12-10 12:43:55.263161	27	2025-12-07 19:54:14.991637
6159085054	2025-12-16 00:12:19.272501	14	2025-12-14 23:52:02.642101
8494703426	2025-12-06 14:49:45.973964	7	2025-12-06 14:48:00.492444
5723466582	2025-12-05 12:15:32.73969	3	2025-12-05 12:15:28.614393
1061814855	2025-12-03 16:26:44.434386	7	2025-12-03 16:15:41.301733
6112363781	2025-12-08 23:56:25.074762	4	2025-12-08 23:54:04.731269
1734027482	2025-12-06 15:09:50.43529	3	2025-12-06 15:09:39.478228
7301764474	2025-12-24 21:02:18.349836	122	2025-11-24 15:03:08.004231
1596154296	2025-12-06 00:11:34.458583	3	2025-12-06 00:11:29.447208
5551439091	2025-12-10 16:24:20.866709	4	2025-12-10 16:23:16.842665
6799734107	2025-12-11 08:58:37.832013	1	2025-12-11 08:58:37.832013
7844185193	2025-12-08 19:54:23.800095	17	2025-12-08 19:13:31.487164
8358336845	2025-12-12 20:24:31.805968	9	2025-12-12 20:16:34.222607
6013670314	2025-12-08 21:06:27.768468	3	2025-12-08 21:06:20.666116
2147421732	2025-12-10 18:44:02.216969	3	2025-12-10 10:14:48.337247
170488932	2025-12-10 19:10:10.704508	3	2025-12-10 19:09:55.748312
6918873688	2025-12-10 07:36:08.798827	5	2025-12-10 07:34:46.320197
6901754242	2025-12-11 09:04:21.62504	6	2025-12-11 08:59:30.819251
8360443949	2025-12-16 19:50:56.916254	9	2025-12-15 09:11:22.887345
5451735544	2025-12-15 00:03:09.471755	8	2025-12-14 23:42:46.022586
8597521762	2025-12-12 20:15:29.383703	1	2025-12-12 20:15:29.383703
7047804555	2025-12-16 09:59:13.890795	6	2025-12-16 09:57:41.563617
8189961029	2025-12-14 07:51:16.932585	9	2025-12-14 07:31:05.914144
7827652929	2025-12-18 00:06:25.240497	18	2025-12-17 04:10:21.39402
7971344936	2025-12-24 13:44:43.558531	9	2025-12-15 18:12:16.007786
7560420076	2025-12-15 04:04:50.518523	19	2025-12-13 04:05:53.306893
1738839153	2025-12-15 13:24:57.425786	57	2025-12-03 00:54:03.291095
5090523346	2025-12-16 14:20:50.742816	14	2025-12-16 14:08:30.749577
6216309591	2025-12-16 17:28:03.943944	10	2025-12-16 17:17:37.512923
7272136730	2025-12-16 17:16:53.748015	1	2025-12-16 17:16:53.748015
5945468182	2025-12-17 01:27:21.21962	19	2025-12-17 01:15:00.897637
8357880060	2025-12-17 01:31:29.204897	13	2025-12-17 00:15:44.274103
5920013494	2025-12-19 05:17:13.691681	16	2025-11-19 17:52:56.040413
8213596906	2025-12-17 01:37:47.370547	9	2025-12-17 01:34:08.331824
5907554483	2025-12-17 03:51:19.389886	6	2025-12-17 03:34:34.791079
5479267800	2025-12-18 01:00:47.750647	31	2025-12-17 02:59:09.391596
2056786537	2025-12-18 00:08:24.548827	12	2025-12-17 03:53:26.956006
5843862754	2025-12-18 00:10:18.320826	8	2025-12-17 03:27:29.297198
6292741991	2025-12-17 10:40:01.400164	7	2025-12-17 10:36:13.537817
1612913307	2025-12-24 20:43:49.383793	8	2025-12-24 20:35:50.766359
1255000645	2025-12-24 21:43:03.462628	3	2025-12-24 21:42:53.78243
7787713526	2025-12-19 16:33:57.525346	1	2025-12-19 16:33:57.525346
5227137974	2025-12-21 18:48:44.966479	22	2025-12-21 18:25:37.114415
5920268239	2025-12-19 18:37:51.411767	3	2025-12-19 18:35:57.755202
7713662771	2025-12-17 11:26:00.600659	5	2025-12-17 11:21:11.191035
8422709162	2025-12-19 18:49:31.778628	3	2025-12-19 18:49:16.916326
7897782049	2025-12-18 18:13:27.224444	11	2025-12-18 16:25:22.697429
6018739379	2025-12-21 19:30:55.850038	3	2025-12-21 19:29:31.586317
8535041016	2025-12-24 21:44:48.801057	3	2025-12-24 21:44:36.987489
487621983	2025-12-19 21:03:58.355872	7	2025-12-19 20:59:19.57793
7034015842	2025-12-21 20:36:54.544096	7	2025-12-21 20:32:28.756632
8450125934	2025-12-20 01:18:30.998293	9	2025-12-20 01:12:37.240404
5332534738	2025-12-20 02:40:21.467237	1	2025-12-20 02:40:21.467237
805318762	2025-12-21 21:59:38.700434	3	2025-12-21 21:59:25.537966
7098716789	2025-12-18 18:23:50.674412	31	2025-12-18 16:24:24.777489
6613279394	2025-12-20 11:56:58.393275	5	2025-12-20 11:55:51.441111
8068061418	2025-12-20 14:27:23.396479	3	2025-12-20 14:27:01.247046
7415359768	2025-12-17 13:47:32.589616	30	2025-12-17 13:28:55.273221
6831298136	2025-12-20 19:56:09.859315	9	2025-12-20 19:50:43.601187
7975512704	2025-12-18 21:54:36.854579	5	2025-12-18 21:52:13.88796
8388546702	2025-12-17 14:26:16.047681	15	2025-12-17 13:51:02.174215
5285734779	2025-12-17 14:28:04.467326	20	2025-12-17 10:35:06.94762
6932856831	2025-12-17 16:16:47.783371	3	2025-12-17 16:15:47.845416
8243249885	2025-12-20 20:03:56.346197	8	2025-12-20 20:02:15.997081
7300111554	2025-12-29 23:30:38.296253	58	2025-12-14 09:59:39.396253
1019557777	2025-12-27 21:31:28.747152	34	2025-12-09 20:55:34.774432
625596166	2025-12-29 23:09:32.162744	38	2025-12-09 20:41:01.210224
8288097205	2026-01-04 09:39:28.061842	29	2025-12-12 09:34:03.828578
8431059443	2025-12-29 23:31:03.973131	33	2025-12-14 09:31:59.200119
7238808048	2025-12-28 20:47:05.925967	34	2025-11-24 18:47:56.872913
8566633996	2025-12-28 00:28:02.436111	79	2025-12-08 23:22:52.804298
6876318627	2025-12-28 13:45:01.912136	24	2025-12-18 20:38:48.620533
5803322217	2026-01-01 19:46:13.162286	53	2025-11-19 17:40:21.515951
7353874683	2025-12-28 17:23:32.275397	16	2025-12-06 17:49:35.865511
7962843287	2025-12-28 21:44:46.666557	39	2025-11-21 18:57:32.420221
6942557751	2025-12-29 13:16:58.152761	18	2025-12-13 09:36:30.45497
535085855	2025-12-31 19:41:37.39768	38	2025-12-09 19:24:43.292966
7967694019	2026-01-04 09:38:46.565437	76	2025-12-09 21:32:58.366856
6521860950	2026-01-05 02:37:07.751167	17	2025-12-15 10:39:49.023378
8063683486	2025-12-17 22:59:33.312584	9	2025-12-17 22:56:12.078965
6193846272	2025-12-20 20:15:52.706516	8	2025-12-20 17:08:19.314554
1916333182	2025-12-19 04:56:57.978443	6	2025-12-19 04:55:01.44827
8547072258	2025-12-21 23:06:41.160325	26	2025-12-21 21:41:06.075193
6593649881	2025-12-21 06:44:40.614906	1	2025-12-21 06:44:40.614906
1931035542	2025-12-19 05:01:22.877696	7	2025-12-19 04:59:30.379461
6640526724	2025-12-19 05:21:59.695624	10	2025-12-19 04:38:21.723422
6237876508	2025-12-21 10:06:50.22514	3	2025-12-21 10:06:39.847762
8057582579	2025-12-18 01:13:06.678091	7	2025-12-18 01:10:44.88395
5874343968	2025-12-21 12:06:56.039763	1	2025-12-21 12:06:56.039763
5747969128	2025-12-19 05:26:47.773362	6	2025-12-19 05:25:18.370471
8164754149	2025-12-18 10:34:48.89199	5	2025-12-18 10:34:24.661788
5863914882	2025-12-18 12:12:42.37229	1	2025-12-18 12:12:42.37229
8508368500	2025-12-21 12:15:41.394439	3	2025-12-21 12:15:35.989491
5457458340	2025-12-19 05:31:10.050646	6	2025-12-19 05:30:16.820959
1884346879	2025-12-21 14:03:59.382798	7	2025-12-21 13:58:41.017799
5794338335	2025-12-19 05:39:51.178729	7	2025-12-19 05:36:56.782052
5142603617	2025-12-22 20:23:44.071855	7	2025-12-22 20:21:45.66723
8405083892	2025-12-22 21:38:16.554644	3	2025-12-22 21:38:10.695366
6474108228	2025-12-23 13:35:56.117266	3	2025-12-23 13:35:52.568039
8012129273	2025-12-23 22:16:31.561715	11	2025-12-23 22:09:39.83968
1271020129	2025-12-24 20:35:37.970428	1	2025-12-24 20:35:37.970428
588853800	2026-01-04 08:33:23.357673	3	2026-01-04 08:33:14.033884
5972522590	2025-12-24 23:28:27.149001	4	2025-12-24 23:27:57.225689
2032446867	2025-12-25 10:27:22.674474	1	2025-12-25 10:27:22.674474
6031182200	2025-12-26 21:34:25.121086	9	2025-12-26 21:24:39.804508
7515588943	2026-01-02 13:45:12.7143	8	2026-01-01 16:43:15.819272
8188198606	2025-12-31 12:29:52.845901	10	2025-12-31 12:20:10.500616
7500700453	2025-12-28 07:20:51.867699	15	2025-12-27 22:41:48.038371
7690405787	2025-12-28 08:17:14.903304	1	2025-12-28 08:17:14.903304
6396777448	2025-12-25 12:16:42.912214	9	2025-12-25 12:05:45.854008
7829152048	2025-12-25 16:45:17.991869	8	2025-12-18 00:30:22.26984
6488362552	2025-12-28 12:20:34.07506	3	2025-12-28 12:19:24.654952
8183646309	2025-12-25 19:00:12.903105	5	2025-12-25 18:59:14.174252
7187275939	2025-12-31 20:38:51.294871	34	2025-12-31 13:23:10.504848
7656004679	2025-12-25 19:47:29.217529	3	2025-12-25 19:47:22.161563
6974994803	2025-12-28 13:54:32.378146	1	2025-12-28 13:54:32.378146
8070335013	2025-12-31 20:39:38.702854	1	2025-12-31 20:39:38.702854
7496081246	2025-12-28 21:45:51.634798	1	2025-12-28 21:45:51.634798
7489371298	2025-12-27 00:48:12.081069	17	2025-12-27 00:34:03.195202
2017915755	2026-01-01 13:48:07.222744	6	2026-01-01 13:45:38.789331
6729691597	2025-12-31 20:48:33.125701	3	2025-12-31 20:48:24.605142
1270464654	2025-12-29 00:19:20.339845	3	2025-12-29 00:19:10.695114
6481602452	2025-12-31 20:50:31.698848	3	2025-12-31 20:48:03.401582
8000547764	2025-12-28 08:37:49.239559	18	2025-12-28 08:18:48.205447
6972231926	2025-12-25 21:41:14.561223	16	2025-12-25 21:21:21.554101
6657222311	2026-01-04 09:26:27.9688	3	2026-01-04 09:26:24.775348
886943236	2025-12-25 23:34:25.920632	1	2025-12-25 23:34:25.920632
8252877204	2025-12-29 01:10:58.151133	13	2025-12-28 19:27:42.852938
7754927894	2025-12-27 14:22:12.675934	1	2025-12-27 14:22:12.675934
8320760396	2025-12-29 06:08:06.017859	3	2025-12-29 05:55:14.718742
6686210515	2026-01-02 14:15:52.279813	7	2026-01-02 14:11:09.878788
7282399450	2025-12-26 01:56:50.046494	11	2025-12-26 01:54:18.206509
7115710839	2025-12-29 10:02:22.99216	1	2025-12-29 10:02:22.99216
1882990777	2025-12-31 22:50:41.928232	1	2025-12-31 22:50:41.928232
6720154305	2026-01-01 18:26:23.361397	3	2026-01-01 18:08:51.049124
5662756526	2025-12-30 00:04:00.284542	22	2025-12-29 23:46:50.353664
6806572470	2026-01-01 19:49:48.586958	3	2026-01-01 19:49:45.071331
6821265614	2025-12-30 13:47:34.935593	1	2025-12-30 13:47:34.935593
2061093227	2025-12-29 14:16:03.018543	19	2025-12-27 01:21:47.176442
1396005389	2025-12-26 13:16:39.289013	3	2025-12-26 13:16:24.362747
5802965449	2026-01-03 03:39:14.952546	3	2026-01-03 03:39:08.488181
7579804219	2026-01-01 03:12:21.953406	9	2026-01-01 03:04:41.968438
7986609398	2025-12-30 20:22:09.905093	1	2025-12-30 20:22:09.905093
7617682298	2025-12-29 19:16:37.363374	5	2025-12-29 19:15:55.572445
8488831706	2025-12-26 18:00:37.774215	7	2025-12-23 00:40:21.81784
6034792451	2025-12-26 18:54:04.629084	3	2025-12-26 18:53:35.141061
8533537899	2025-12-31 15:28:28.64584	9	2025-12-31 15:23:54.359699
8329946072	2025-12-26 19:34:52.732754	15	2025-12-26 09:19:24.383895
5604698232	2026-01-01 16:39:53.270473	13	2026-01-01 12:36:00.525758
7428775931	2025-12-28 10:39:31.212864	12	2025-12-18 00:40:06.768771
6594831541	2026-01-01 20:48:05.378264	6	2026-01-01 20:42:03.086159
6617326165	2025-12-27 20:57:58.824082	50	2025-12-14 23:04:53.69882
7651318299	2025-12-30 21:07:04.778871	7	2025-12-30 21:03:53.154655
7709657130	2025-12-27 22:41:20.637939	3	2025-12-27 22:41:18.093678
7391083654	2026-01-04 13:17:42.093195	5	2026-01-04 13:16:26.950805
1529462562	2025-12-31 01:00:03.255325	3	2025-12-31 00:59:55.576046
6417435504	2026-01-01 16:41:27.96752	5	2026-01-01 16:40:44.454807
6588157830	2026-01-03 03:41:39.231817	5	2026-01-03 03:40:06.849491
7815565723	2025-12-31 16:23:16.790351	11	2025-12-31 16:08:49.258939
6203399221	2025-12-29 20:25:33.393233	11	2025-12-29 20:22:55.489415
5112004413	2026-01-01 23:56:51.8296	15	2026-01-01 17:44:41.797127
7126354599	2026-01-04 17:26:45.440276	5	2026-01-04 17:25:12.283852
8586830891	2026-01-03 21:57:00.682044	15	2026-01-03 21:48:00.264427
7353034266	2026-01-04 17:59:56.059474	1	2026-01-04 17:59:56.059474
8360661555	2026-01-04 19:59:00.196524	1	2026-01-04 19:59:00.196524
8501550749	2026-01-04 22:53:04.979946	1	2026-01-04 22:53:04.979946
8573784088	2026-01-05 04:12:23.575025	1	2026-01-05 04:12:23.575025
6848720005	2026-01-01 17:19:50.80828	555	2025-11-23 01:35:56.739315
5689065087	2026-01-05 10:57:17.947112	90	2025-11-10 11:42:33.374409
8257807182	2026-01-03 19:08:52.889201	15	2026-01-03 18:13:20.393091
8377242910	2026-01-03 19:09:45.603675	32	2025-12-18 13:46:25.384286
8583782309	2026-01-03 21:03:12.44136	1	2026-01-03 21:03:12.44136
8005019736	2026-01-03 10:28:53.620364	14	2026-01-03 10:23:09.868434
7792750331	2026-01-02 13:39:36.714793	21	2026-01-01 15:11:43.297123
7555800019	2026-01-03 23:05:56.492232	128	2025-11-25 08:46:52.181113
5496021107	2026-01-03 16:27:01.194597	1	2026-01-03 16:27:01.194597
1992060940	2026-01-03 17:51:29.204094	103	2025-10-15 07:38:24.807346
8412989087	2026-01-03 21:44:19.195746	5	2026-01-03 21:41:11.517029
5700146507	2026-01-04 01:26:07.931841	3	2026-01-04 01:16:11.275078
1013148420	2026-01-04 07:23:17.954921	44	2025-09-28 16:13:59.097308
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: telegram_user
--

COPY public.users (id, phone, session, options, current_rule) FROM stdin;
7467184777	+85571 460 7794	1BVtsOMgBu4BAjaH34JkFpYCe3xBVgrT4zUV-C8EHPf6rAdZnWKOHqhd7MgkASKkuJhhFRlD1bZxeNuEXZJ5_l1jqPW_NPO0WkhQ95-MeWcRljSgr-2mYVVrsUCjp7UQvINZrudwh0tFBq3o4r0N-033px33TfbqYoPwUq5gwcvH-1U4jZkJYEmxvsmnbNat2sGxxO7J34ApKPdoxNrCoIjDapV2tsb_wZ6zHwZ_2o7YkqGfD41GUScgytfh6RJazYTjwf13VMZeJJZxc0PSRDvL4UnKchzh3gk6UWFRv8vACoh51nXEWgOcqm2U3ivgw8e38W__vftZ54KsiFTs6xh0RfIhNpFo=	{}	default
7714089439	+12132960174	1AZWarzMBuw7bZDIwjobNP65jtnuStwe_4y99_MhbOc5RGy3rkuYF9eFF9fWEl4zM8zOmQOf5-stVY5tA_SoKHJlsnbj7AkFoqumLPVIYMHFDrkfNn40m777LSNvwXNF_nBAZvVMIOaYh9H-n51jijTJVE132Iiy6ERGXtiJoif5cMJTb7hT_0Y3jmMVy7rX5miPKGeUEuY-TKRC01ZMwdU6INgiZoDKf1_L4qZ8wk5JIKJk8zblR3ba0aOf_Zb8mBw7nCAE1wpFdNO198QQs8rE6EtamCDxlfnMxA_SXiuFHiwBWD_6FgGlCzIm4-0F1wf8InGTFxiqnyk9DcmV6lcDWhjGVPSk=	{}	rule_860315
7291979622	+639930133186	1BVtsOG4BuzqFBJts-LEXt4-dQqxmuTGQKrHb5YBUWCkDF3WGqMBIgU05fQc2aXEB7FwU4H2ku1PuRok_DYWMo1c-xUTalCWqttjPBEb0seX4TvG7-hlpwd3RBB07Xu6lghiwGn540xIx1z3OeJ-in_VQM0xy2GCJ-pAN-BWkfa9j2IJBBJJ4BGkkus4WfDmjQhxeV-YsGxgDo_7zyF726U5bx4S78J5YUyHHB7_Q-_VO-ei-bqhoInHy3BYKrtR--7QpZ2COWRQtCkNzJWMqESQaWcgf9jLt1-dJuA609ImtDUMcsnGj0xNGa_Et7JsfE-3zAR2yqaepsu72ZV9IBav4gCklnDc=	{}	default
5081757613	+918987569083	1BVtsOIsBuy7CymOb6bCn7iHeM7oLA_sl7uP9FsCqSxXyh0-ME3BUZ-FY3UHL6XGMOiyryWO2AkLe3J03xob8FQAHkNwl6q7DBH8lvdyia9_kCN43IavuOxiWyjdqH9r9PyV-2gerH6YbxN--9bX91_-T_GhEYfoTInxWBFiqXM_O9eNpoe9q403ievJmsUubgCwYCHRyDpALhkhn3An5QK5A8Lv9g2H-VI4AGR-eWjJ_JkNgjx1wFMAikihj7BPI4jL5oLRiErGPprtzc19givvTFGpWJ4-lSU8nE1P2lgdWt3wOeIqPs8ICo_AR34g7k1zhYiIJVGrL68_HlmucrhwZG9Dnfow=	{}	rule_253652
8083890417	+918424085751	1BVtsOJcBu5Or85UW3_shBchbzSPe-Y6anDEdiHlv2gwtf8IIXRxrSDqt-Pul5-qljpeSJQUnb_K77SQWxENGbxG50bN3t_eQeHdrWbW_QOgYq3sNfQ8oIAcFRxh4Eu0L74w6LvDbYxSpZmTbLexUtBmSnv-VfxJaowLIf728FjPZzM1dsJWZws2MqKplYx4WAEpJercJ9OinaKY3kyh67ZdRFjrIHbDIQvvTg6Cviavd6Lh4OMraBp-axT7mkhgqghX81KY4j482LswKDeZG1ymr8VV9mizXBSKbGGIVW8YfDmSxUfF14-ZcHkEjCm3xkik15ZeHGtji544vaQiMAWkx22aMGFE=	{}	rule_452475
906648890	+917480890164	1BVtsOMABuw0IAiNYUZpa9_O7ZaJerMjd_lv7_1Ba5VW241j8YqsjJGPrgD3edL6kn966aTasEewiDs3UXjpc8n3QEa_JztUAGyKgGlUM8ca5D9Uj0qfqNyTIG9A48iHdkXB_5Ot89dHOcvnme-sxR8HgCd1-d4X9b5TT-2fI9fBxw5fpnLhcuMOGG5Bmj6_2ztXjzoKoxQZbMNSm9GSWKAJVX0uHdL7M38Mqe0TV9e9gPebQtT4Qfk0DeKmx5fb9cYkKPSy5Lf7Jya7R4HFtoykHfe9DsNnT9iwh0g4ledMY5Zos-EE0KxvhEonkLtFaxK8pBgkhfiYGKGHpLE7zgGRYhXksK34=	{}	rule_571989
8064447179	+91 74052 86204	1BVtsOJcBu6OZIB-Q4YOWDllfBsdg4Eh0i511vw4oN_5TULcJ5e4m_di7hZphC103KXt-eFYQxvnn0S_cnrNj2aiE5GRRppCR_u0upj7uDHHeRQx6BLmM9A0O7j8-v_e-BQXFuTes9oB8BaAciHuIb1EePYB-74I5I0dszvhmXmX5FpVyF8KtWdUA5HGO83TUOd_lYBm0RjVbeG6n-X7LhcFzrja1wkcTWbOpcdLPAuqMJhkAN--uu8pVRwTycW3E9OoFVbrUb-gc1NnNOsgBSGojJ9V0HEAuPi2bK75IqKuUSyJ_e178xl-LSKzTZJHffVMRZKITBDvJyIl449ig9w2n7Q3c5nk=	{}	rule_475987
7123794523	+880 1908926106	1BVtsOIIBu3hHcrG3pksMhXuEdmRgBJqXCDt65UIO8Nvmyn-YdfD9LNbvEkP06iAWmt_LPriMZJSzzG3VX0icQdF1HfkEhO9Ul2G5TuFsG7yKvL66YNHasFpuRWbuACFhlKMf-eaKIqH9vM03LJaliyiZQmWeJlrPgxVTHLRi0ClSX3Gj62xmMlJeKnD8lqGEoTKu0OwDKFJJ0wQk47-i9ZVIyIBbizY3N4q4gYfp_XuSqwCk4d8MlPz8xyr_D4mBAe4x7ao2wMDbDJ4sR7dAf6PkLsfr1sg1cavyzIFM4Pblc8alQidRi40daAocRggUOlvmYfOfzE_19U144FKE6YkGwgf0t3s=	{}	rule_568133
6434063803	+8801409433729	1BVtsOIIBu3kTciOpVfGQZv787s_rGFg-zytcWvRRK0h2S7Q276boro7iH6h5CmKI6RWyTSIvMsNJrjy-Xn_4etJZWdrqAyhGSp1SAtQlv-if2Mw2wZbgsRkn8MI5s2wiUptHHIkvnuza95rHUvZGH_nUsanlJMKMHBBPMV61Zkw1Zu9YRkiE2zQ8fr9TWGGxnTA-_w-bP6EsazUiNprauVpuInU9MgAYP0qMQegy1HAi5XSOI2V3n1dmefzXqNX4w7KmkaGPo-hby8NOiGPJdNUSu4WIKiz041b2VlBXzlyuX0i1IreAY09O-tGh0QKE71pjKShivkeqXU0HRLd0mteN-ENowEI=	{}	rule_920978
7096845088	+8801996987881	1BVtsOL0Bu6W4yvHB103zc0oC8XITFA_LFmacwrKokUxr9jbxOwdXuGhkGkMvu8gHbeghBViGFDufPh9p80t5Rx_IcYGgiGJwaCpjKmDZVP8H7h-1xH9mis8R6eAvyOXYxB5iLG3eFKTWbS-YTHtxgRkmv8AAb0gKFHyvwTndS7wvtxhag9rV9xNMv7Nqo0UT7v6uWFyyEb7pDmsehzQRwUfVJvk8RhT5l44H2dZUvlFMbcHfKfiA_WvhytiwyzieoTw3s9FfMkNWlsmonsFVYG6Nn0N2fYRi9HFOnfn9MJe1K0G5kTic7w8NYkC17SYiOgoJ9idirWnzLeMccGr-6R8w_YlI8uI=	{}	rule_865114
1604618552	+8801409433717	1BVtsOIIBuyJWVo3YIrkfmaWL5Mp_qweC5AQ5EytypDBT04IEyUE46NrKJN-Shkyz3ArlaqMdqA4YhOsDXetZP2b7GKfCBauBBNb3LklUpAhnkaAEXlCNGEzBXdGVodLBm68YUP8RpUIJ_bkB5MHwzPzFJAKNNh3bKcVaBl2NCBcO05JVw11bIXvC0NRuuTQDNqwxXXXWciTb9MaybHdT6pBmldMOUb2munUczjmeTVx907OHfQviJc3RXbBT1PTB4owmrh5t3Nz-BulujGl6oOwZ9O1x1Dig2iakDbkVkIIrbUVAxtVxh_sQMTqj0ruBQpC3UrSDGApyPxoKr66pSI9VQeNV7So=	{}	rule_1090170
1013148420	+918084547784	1BVtsOGQBu71m5OQ7t2takt36SkB5Z-phC7Ehy9vArwVzCbQli13SS8PwXpL81YhzN1UCuU3s1OfX86M-DpXmraEVDjgGYuhoSXdtl_ELQ-j2RyKLYC8x498fv0eNbDxOF-CnXhVVjWgN5jf_UeX0OJBK2IArexDvJkfrSysv5ygZR--L8V9ABjMPw-iykGA02Y4xHBM9S7Z1Vna1t69UubsctPX0yJHNUZLZ-fXsoSe_58ZsOga-4eA9BP-sAvnCP8z5Kty8gvwzvRfTdqmzskCRTgEfY68edw8d-k-FKl_KMV9gIsK73jADliuaboYa09c3P3ZKQWw3m0twRi0p8TYJqlFMFEE=	{}	rule_706016
5773544941	+919534076181	1BVtsOIIBuwxClxXiER7b5aOGXewaE8r_zk_AsZy8ylJVjiPO1nWIC7KF1H6bJXvrwwplMqvnvRSYXcO4OFHpzA6vA3xCrxfEAFgwmPHrNHaV2rTAuWA6ZWux6N0n1jVtZZeq-AYW8JF0SD8-QrZdQoqOHIiynjPs9Um-5u_17f1MKdpoXYNz_AuuT45n46ICHtxIabzMubmQugJmibG7ABnc6LwSQl2GXR1BuX7bEfvT6CceqcwEesd4O5iBuowTzBpnJ2JaPF79xxMQYHqbZrOsNsufWOohrc-EFioxNl43IZue-UfHkYUDfrWes4vIeQ4cY4A3MVfughHzt1Y5gsOAlHyvG8w=	{}	rule_1173686
809117482	+917899891936	1BVtsOG4Bu0PSooudW6anMpWc0qhzvAkfChth4kGx09SOB-TxPqFzvGrIC5KaanaWcNfYnXCJlMtQ6YH7ZSKWBAVh5yWIbHf9j2INX6UtPpOl-HPti0vE-iB9ojt18fTNPeosxWFlOzjyUcHu33UTQXrAjzHBj-iUR5RsZXxZsYMgBfRebLXHPTs2sGmVmf8d2xUCfKBuEFE6M8DupxJxSeAihttbjBl227CFQO61EWd7xKqxP-JYXDVHBaVrfmN4LPAdJl_Jy2Pu32jGGFYUtYDJYd6bRu-umirBnQbcCWsglRQIuh-EPdP_B0C65lrph_jpJq_3OKXC_9M8Vf-HdpFtwgA4QiE=	{}	rule_233411
7162132327	+51952154749	1AZWarzMBu5JMoASF0RIf7JFIgeGNpeAfEnCFK2COLKwLHXI6ZCWJyKDqhCUk2y3or2cN7V2hjdrHreXa1sUDZQrLY6yLeZJ1Fh_pqcNaEJJTT066eUcZUKzpvR4OYrdn_FGaxn9S3iei2d8LLcjmmV_Blt8gEY6_lIbW4xZxuauYtlYymo0GelAUYTg2nZzAG7CWKuY7hKS4Onux_SpnLLmx728gz6LR1WiD-wH-jR90set7QhpzAcTroNnf0S0AO5pq51OU0H-qSvMkOBZ8v1cC64e_ABzAFLVgllcpRZQZ2UuBrlASMwkiV4CllLP6R7zj36xewCz6bfsIIPlF3Rf4TNNbiSY=	{}	rule_827135
7337643152	+923335129588	1BJWap1wBuzdm6AQtZJjqpRBVGPn13Q7QtUcCt5CQzOlylV5OrGBUyUwaG21w7bmlh5kI_0gieMjPeNFIqTV1pW2VAfZioE5wz_1YYxBtFzQ_GsF4hbiWAVlIk0izSgt5BYOpOPmScfT4qLoILjCpOXI_DqxcSXXMTbNLKmkQY9QiwvwxXVXt5vYjQ50LgE0KOMQOjXQq0ZkAxnUEC-9qdWqvFfkab7tkWP2oXzLlbPB8dsIQ2g6nucMgptnBBde7-Vz3S10jrqZV8QE8yh8ER8B1yHVd7_rxHJX94XV0mLUFSeo5WWak1BC2YfsNV_dPpbLPHNC_hdvERRsujZi6oUKJXT5h7KU=	{}	rule_779226
8495094059	+919905950172	1BVtsOIIBu0VX3DMPFUbZpp-xx4Ic1RWIOs4uXv7m8xbb3XEPg-SIhkUdeyGfaszSu_4A8_iFWxPZu6sqzTvLX33kvfA_d6gkcolTFWCEyJefgFr6qHPuZXo7TG-wZ4aPrN3KGtpNld_F9pkrB4FiiOnQrX4iB0vE99RUveUdRoTKv99tSICR9r8jCXG8GF6H1wKLZZIT1wEE5kacVIgJIGn8SOiN7PFAFyjaO2dwgfYbpo00IC6j1K-vHC3LQ33GfX80bKZbU_L2ui_p1YNrfpWOC9Gz02NNH0SLDxITHFpmPjEZn7Yo0kLnlLpSPPrkn9vXVeh7HYkX2v9Ly-vJTFM4Z2Tqv7M=	{}	rule_1198411
8215282057	+917766856545	1BVtsOLIBu6BXSUm8XJLYZZRvDw4iJxJl-0gwZ4uHlpfDFtSILWM8cNY-yA5NC0hHigdxdriuztSa-pz5T5Y2d_ILEhuL-JpGM35DHSSdNXAtDGOdKneGeIIP7eXZzQaeqvQL_58eDbcofpNGhx5CwQd6cbZ8XupuMljfQG-ib8lOBHiNvrJx9VkOd0KHzTh-X1PyVxx80zmroOLL9_1tsRThAwbyTc-fNhKSNcga4B3qA3Fzr9HLKmfsYmRIJ9-qTi2snYOzyXyOAY1_qsYchcDIQQWQcCbt3kA1l1hd9z3yqc_fQEJm3WR_-fyrssNE23Q34dyh-sUmbZZY48QnSWIJ2uob--4=	{}	rule_1414695
6222156706	+491706916397	1ApWapzMBu2vC6mRQ_OlxlxF2UEwgM-R4d1UeLPhtXXMsaoXWZr02mozk3_OvPXry5eL7s3uuako-vbKlTqgloXEERbkzeaK3PJhS4JacgYI4ArM1ji0ZvYmLh2GNowdEpqXJ7aEQT_VSzpUdnzpmGfmPstQ536rynTqwGaveNUKikdKViL0LW2UIWd3WnwxzvtAzNyuAEedhfqvhEoRxq1dBIfwoqsqqlgp0NisooL141PnLmxv3at2uVCkSRb64NAPppJNkKFV3eMO0_a-P2HfoUvny1X1uhlRWv6n5fy2MmMG6P1iWM1YPfIJSKGEbArZwwI6zIlzqznGEFU2wg7iiTqA_3ZI=	{}	rule_1202605
6251096236	+917078282573	1BVtsOMQBu3EqP-IJIQ2YXfAhq_PeSI0UkPKuPCktXMSV3wK_po5zorm_TidXXpJ5JdN86PmSJ2G3MtX_L20hvWtnAabzDLaH1zHLBf1XrSRU_uoWajol0k3z9cb30mBTjC4GpbSKvv50XpTiqDax8_X7JkJqKRJWm7VIg4xrlkN_jX0yu519FjUPkdSqm-uSShiOTGZF3alfu8z0GmDo5Q6GNBeiMYJE5u2Q9Cv_fKczdYo76TfZ5C2hw1cISR4F5lYVJZW09aBbyCJhmeCodGCC3fUk0NA1scynB_E9Q7HiGLHEXlUw0MuU1kuqhXRIQZP4CK8Cj-u_ZF1KffAVYiP0fSJQJJk=	{}	rule_1462816
7941190412	+919812719854	1BVtsOIIBu1aynVYyhQ_hWB9zpVEw8G1cYiaH5qr9RjN8kB7Sg3rD-aIcmZd7njiRQYUWpENLLuR8LT_bdKa8jliFwE44TzoraArmpRL7E1_JQ9yhy_XzilRlWG0vNn-4VND7i4D3FN52h1naZldei80CP1b0TlmaJal0rNFl7Xiaq9gHzr2i7MZvgkfZiuu790Hn0mxklAloZXsWKEDxGamqkVJsUjEE-R28m5TRLG4zo54ibS-LEJFRu2SJhs62xTb0vwfaHut57JACSe2WiC5JFJ3DDJbkYQrmK11XOVDiZmPpPV3-QGHr0dANRVZdRfcge2nso_LLVZgDhEORqnLvxI8jGPw=	{}	rule_1195456
1327566897	+971566266090	1BJWap1sBu6Q1MRMEOYveVfa8t7VG01K087DuKBuXHTUNbsHW8MS5lCBGK0wJxnd0pyEjdW-c5vQh6vmAhPPkp7PScIKVMjzKIpQAzDTDH49UVJ5BzxO1P6NrsnwcqRabnzcENwmfv0gUEU-E5LZGVaRHgk6Gp7w04XV7mYxrM4kXkVgIf04xnoASCe3LEjaiIsMji_mGZ-ZvDK6fBiBD2TqBjWzRgdbag-UpoScGPV57-r_SZlbKChcvtnTNo_mz1dy7YmPBysxWyRR9MEzngDiv1MjAkaNV-51dA2dh4q_PLTQgvfiR_0drcwHqxxFQgGqCqAgjOPS5cd7YoItuLZy4kzRHq_A=	{}	rule_1323614
8282805291	+919825943390	1BVtsOL0Buy7dnGK8QIH3aUjaZgPXEQlfFZyWcsGqqeOBeiBerbSp3j6SI5HePQnEeQIreuhnLb0hFfLhP6tOjIvbk3hStp-2n5IYvJHjQ4A2NPDoaI7jSG0Gu3TUpyx6NxlPJDNOnQaXuBvQWwR4_KMv8kqpaSPqSACCJYOvlcmDQUaX3A6daw0FuLz5qK4N_H4AzKWwb9dAID7IxcXKEpYPbOpYnFAEUIcw31gbEHISbaplt1uLiwpxczHuZFl9SRcsdf4cEuMghNLWJbFlbx5e4c6Dw_pTef3TDDiN3suBog8PG7GuzoO7LT4kPpbgllzsFUb0guVlgZezk3Z37QzJE9RxGT8=	{}	rule_1453303
7404167930	+919620425650	1BVtsOIIBu44cOTrN0Nx9EHgFxAjg0nO--q370wMAvwhpepyx0PjxYaMt4mSOIXUNUox0DSIJygyqF3K4MDbL_DkiCk-ktIv9RdRpUcHEygPG2kEfHi7RuWzyOs9Nwc9mYit647ZPMVa8jgTLoy-s4xS8tnb3BzQ_TObsD1-y-5I3UCyqcMqVhdFQ8VqpnPCDUTLCW1dnH_9HBhrtBhAAEOeMij0_NGWZon2cQxBrtK_rJe_RaHgxdBBc3aXxEpoRtpjaFCF3070vD1teJvFkyl_KF0zHmccvLqyCTVK5bhgb7b-xj5KBmBTuWMSCNlLj1b2G9vjitKEIhYLa98Ez5KOzzG79o6U=	{}	rule_1121253
7849204364	+8801308463879	1BVtsOK4BuwcTf74IMtvpfsoIQtJ-m7BrhqeQtdZolknSvz4Bb_WBC8a8klzXa5pnX3NYTLG3wGWl8LjPzYiil3CX-3gAJ_YMUl9mcb2cHZ6BgfRjUD-cr_c_-AyKXYwHYFaFIQ4vIqTaNr_p8OqHd9donlLM6OEiIpsteYq1v7mWUw-KZfWWMEIBodVFjEhSP8tOmSn64UBfOOPlQfCx9NKJ6rATYd4UQUrcSLReemwZipUv7S6KJDoiKrc1APwboxRo4U6EffJar4tesm0DyFoEjDOBQNLJXveFg5NioDYxzNfLZI5YJeYisJuzFdqZpFz2HUNHzvE9z3k4LbixEJrdcrTTeLs=	{}	rule_1405271
7065067748	+923335129588	1BJWap1wBuzODbhEg1zIk6hc-RDPrRCXDwZ_atXVILM5_ERW_0FcmfGSLXJt22uS56t1PEwCqoKJ4g_W8EDXgbfi1zh0BDPHhj7o6nUMGcyf7nMzJ2EHeXLrZmc9Pbr3S4ygltMImPn968HOCMLRNI8KgrnGO4dc0tG-pSW8pxnwWmyKh65wuyLcYwBGxt-6Kxl-RqUohmDzCh8kaFOiwSI_XgTwVL82az9Cik9fmFMOO1Wm91bhaoo6_FHSwShBQUDGRtx8IfQtYTvfk_XIrXIjqXTXX0fT-vkfOJV5z5a9A26dH5jwthCpvQWBRevwRt1jykPStN3U9ZbArLR_a00IEdDaD4eg=	{}	rule_919674
2038045502	+8801402403156	1BVtsOL0Bu0W2Id0yX1o7S6QPCCQBtb3hECrxb2SAjso943qKoj__KNN9SrcV1PieH0LBIGJeV0LoVA9Cn6uxRbpP22Il-v02C8q-RtS2LWjAnzR6MIqcK6HXsR2-dvjXxQFKOWJxX3_6mw3g9ntfF-E2pehCA1clj0-RJhZQCW5R53bS4VlRoE4ATsu6SK62eM3jokT5I8AryWFaablsxVvbzy0T1dFDPZiRe7wJsGKDevX4C09bDjNyr3ReaurPaWskCxlYL12d6uCh5-z_y3iKUOXGQg5wtvSYsaZjynjghzH_eD33cF9zx-jAwdb924FMwxbowPg8hJE1CvJKPLGZ9SwYRi8=	{}	rule_1477019
7154763189	+919031796102	1BVtsOMQBu7Uc5MyPkrKsrd3OIXvFaKlOF79xbeAwDbNvnaFYiHzo5IYw8rr2UJ-_kEo0bW7-QS2w6M5efabuuQCCRxHnou6Exz_ZbJsRHUMNrGFEuxdp6KkreepTUzq31mZoYPWNqCnh5pN6fHW-vlIZg9slEZjzFaadK5cJxuAaZDgg1V92cfzdVeTZy5dy6VatPt55v6QSHJaFnBJBzJ_5CMh1qEwpiUG-ttdu7W4SBVtLJBUkobLC7dVTocAWgxsVSq5lsO8XOuyYwaynMB1tRozoufX0DtG5c8lDCmePEvYZbFvZvPlPtAmjAMl6Hnr64Xwokodnxadulg5EpBnOJ-KRWv8=	{}	rule_1529434
742895166	+919146084246	1BVtsOLIBu1_KuUxP4U38gzCF9Z5jQDb34EnV0tnBdTQV8A7x9dY93aA5BdPwQ4rdLFJyYL_V9g4nY5nL-rQLffsfHErhn3NR5zw9IGDcgpNy_-G3YeXEw2p7bplV4qbygMH6sETDhM5owP1AEgoIrpsGNI9B0qFOIrIlaayDhWM53ex1rVrC7V1uKu50XXdeZqex0dm7aA7D1MRgTpq4skMv-zZqtCeHklG5LMJ4h7mMNS45oAT79045WIx38vRcpDFIoLNFEIZ64a1rfTjA--jNA4-J55YBTm20r0rrOI7EdSR9BgRMeEfv7X5Epzu_2iGN2qlDltyhefWL8IDobxv9-7qU0Lg=	{}	rule_502088
6532735248	+919263774275	1BVtsOKEBuxbFogdseB6krLoI14TzJ7icnaNut0nZ_EjyyvbFD7cYEF5eKhpqex-rKTA0O2yfe1IVZ4mmTR4jM1ot-Wm-k4CW0jsf6lpVQKwQInd7cVfME87jfoh6UMcLh3mrjYgkge1iXBR9NGI2x0F8fyLihf1CYaXa3y98J0LIVR0c5yT47sAbARkgEwsVi9lcFYKxtAGhKsuxE39k8ti3E8-KTV4iaCC7fo1odpRUz9VY_2RcQxM4T5MnDO6x17hRHL5DurehvGa0jz7st-aRkPwBAGzyRRufandT5Kzlio7wxPYsrF_tSBaDyrw0_9kXjMRZ_5NjNMmGM0Ij3nrTLGGTTkk=	{}	rule_1597589
7251995251	+917508081212	1BVtsOL0Bu0qVN2bVbS0XvZ0UWO_NSi4CXiz-iLJhA1UjjjyD1cFWNTsjJJsoL8sKorxbujNmaKUAI2Ikbz9-tGhfwJ-PXsrvfUJ23VvuDq0ztYe3CSqMHXD-o4c6kZfkReYiqjWGUAnEWiecNz6wzs24xkEYGHTNL5M4oKANZPiYvVieY6_I59QJwXG7r9OxCLg3uaHJWinFm7OIQ-xcHqHlGOkGvDTL7rX62BF7Z3h1-16jQ-jqu6PTRfYIMvtTQlpjy1IgJDrmiDnfnljd6lhYiJduITeDELMWFJT2Hkz9rOaU09451q3oIw6Z2hQyhl5FnMNH4ThO3zjt4KQYSxi2VrPOhFc=	{}	rule_2566221
1429618267	+916205511916	1BVtsOMMBu3uR915fuZDm_wrNiboVva12SEfubmCbX0hH4a-9V76z7UwZ_MTBSRLW14dbLVPvf_w5wzfS8NulyskxOwmy53F8XvpenK-h2vl0zo6vZdf_W_Qh6US3ignoH8QvKv9gcwd706ypcgmcBTK9h_1HPxzJ2Mk_hBERET47mU-3b6lx2TwdKMSA71zhO5quFI3tCorzmROJK0rRtwO0E_ozN5WxQUf-CSs2N_NoOWvVm2O5exFTO5UtnFFsc17X0g2wgb7SZANFX5i34d8Dr1c3IWBW0VTCKUrUkMd5sBQPCU4ltD1rA1hDS-LuwtpIzrkwVmsBNEqWcHyPty2cuLQKqsI=	{}	rule_1867318
6654944138	+918606055862	1BVtsOK4Bu6bFDCoaPOuy4njXnGfFlE9nh1c_gJgLUfyR861ooerIF76ylL_sXBcWgQ69cGxAwP803hILpKe_zR7gjaYj9NZpCDOcPbrOUFjj_SgW5XLnvrQO3if7d7OzCzLr_Lhn8eXMda6A7oc8_gMhS8jOFlUVzGzSXwvoDXPFHC3PvYhwB88HVlg03P-ZK9YtHb1TZp-YHiHBKDJmr7a1KYaQVMBOES0h-BLEOeUXDR0Q1lxoE7fF9O4BC8nKaBJikTpGLqAa0LJg1kDFV28CKPGeuHPpdYRvwo13sOF4fuATVskY6-9btWZAyXqURhvOawnbJib8exZx7Ijk2aL5b0DTMt4=	{}	rule_1602200
7144330602	+923153019139	1BJWap1sBuxx0ZyDHdSHXitNuREgLKubbT3WcmfL0Wmh6tm41e_A7ImY4J5EI8MnU5PSxGKrAKw2QJwQmhBq9TGgJeXgQ-OWtBbbSCWaRU-FmpX0jw5DfDzLGFw-JE-jmY1rIqlwuWKPFxyNBKpubkUFesTQSQ6J5_cXsZqqBdsysFI5CXnaSF6uY68GZ_iGMBBW1VunfjMNgQcCg_qpq7YcjKiYMfTTa7TqyBfL4T9gGE7eTkJ-hM4IjbakUh46KDtKEE6DhIcuSFk1qVNVyfL1E8rW0B1XDBjcPXL1R-gv5ZqA3mokEMWq19COokF0jA2EFtoAN_4yiEEY4QSTVJdthDz7fFEk=	{}	rule_1739276
7611856186	+4915110288902	1ApWapzMBu28UvncJhOuy_1F-q80wqc16xErFQTqYaYunMwk5Yra6acA0-D_kePfTkBZlXGpg56pQXMsxei2V0Uuvvdlq0gr4zdJyrP9Stvicdgy2ytE0YSizf7jz5EyTX9iwLLT0tl9A2FG8IzhRADn5xYrY_0s6LBUnnWnMT8GEnl9nCIuePeIOaxSGGVeV6uODkD1pYWyljsgv9rssdo8Em3Q134RJsb4e03_Nbxmm7hflskMLzoO9_72G8_qU15vw7GWNp0Z5RUi_RR-UhDB_70O3TjWeItGMmSlQJqmyHdmwapHXHZKEx83lIiEueVWIDocA7MEGGhrJzPG_nL9zd5FESVQ=	{}	rule_1571852
7693090424	+918476986289	1BVtsOMMBu5iaQpbym_c4tuGC0iBI1F3Nwa1XB-Ep5f17AL6EnOjoxqH4tXM_MwP--qO9-4JZ_9LnB8Lk4es2swKi9_jXojmvWTASC7QucAaOVYSnKAZbjY75-ESFG1n5mR2j7zOzbtw2ixMkXkJCuv1YWHz7kmv-2YQ7BLsDupYeclROjsp5ln9_Ee0pOR1SKZw_XAXOEY7Ha6y3OGoHqFP456qP35ZgPyzs96KACR99qaqhiUjnFi15xJFH1qd-BcdQYrElBUQqAfpynbzlajSgwXt71dQCTvGSG2TfQBzyXdtdjyiCyXlo-SOjs7O7MMrFtrIfW6e5viDDFpE28WDu0BmgC3A=	{}	rule_1788236
8258901462	+918178355598	1BVtsOIUBuxOj-0R6guMwCaVrYzVmPjFn_sAF215i5y5-SmHO8nR5Ip4-1omCxf0h3Beb_1TW6a7EsE-_VKGWA9eK50BiTT-DAMSZ7d17ujisa3Jrt717WTsblYQ-nvCCpaF1dnw-S_HGETDkzecCdNncPb52p3pTgW6f9ohTFISRDUSgcFe243r__9BkC7nYgjQUgLsTr1MroBLjMqx7ke7uz_uFd9LSYcbBjb9k33r9UPaTFUpikghAOC6A6ZVyIMAO2xLh3FOHWZ8G5xCSRRk88WwuiYETpmQR8d8QKvVifPbKBndMY0nJblt3RdtqIF7MledEk9zAT_aG5TYsb--YPkfqlkE=	{}	rule_2210712
6799961892	+919651867723	1BVtsOMMBuwr5LX-mbSuOOSuVCL8DXzekKAL2DZGF6cgI-ROWKeEXnQEYzOhfRMkzo7x3iOn9IymE6mbNrXZ4x8W-rGuofsaXeL3dBkNuzTzcoRpLL6mU7-xbhaxXCTZIRpqEyCUTk68e3TcFhvRyW3LqJUxyOMLCLRl6pAafRlyMBqHlHEEoLsjV5V4l939kWD2MxD76JTWk_htRFypWojCHBh6tyHJRDSh4aZFEtK7VRf2qCxR3WJ8PcDn36f2zzhaO5pZohi4vdBh8gQCT6kJ0LPrzEO4hYgRNrDwRM7VUOgclWz5Wi87GXN8--h8LIOi6fMIxUdQr90E8vKozcSGShwz6jL4=	{}	rule_1788421
6651813666	+919801211737	1BVtsOMMBuzTnpFfyxcDsIcvDIWmnDSf6UOjxBua7GXobj22Goa1-QqOVG0asGK_BYNkCcZNBzsl9dPKxrpm7-Ff9hFOEDw7j-vuKFrjNO5cNQdMo6WTimTIFdm0SKlxRMSVzZVJIIye7uw-uibSgb6RLb9M7NeQQCgveAvrhNb9quav53x65cTmVS5keAyD-HbUh2pLJXRcOjPGJt0nr-hbMjMkTatrJVQVjPZJVF9VS3H2-yVQhB8RxuJVj5oXYyzgK_JsbBBR2LUDTHcFhu6adyUyOmWPIuLu8tNr_yp9n7lGuuECfJ-DVH9DOSfjKAyJuJH2IsVcuKDuzE6eLxkmjhUlCobk=	{}	rule_1797231
6059788941	+919424903507	1BVtsOG8Buz9A_KZUijxukIZ9jsIVK-eHRJw9ZZxWJ8OlpJUIW6Pv85bG8KMfwTHaXSU9c5wTTa0eQyfq-O6oDBbYaadpv_h_PrCgDAMLSqPdXMz94uZfFl6zqkF-rn753cMQOdH1WryQ-Q_au8yGkAB7MbrHO6d6TuwfxXrgn8l6ntIVfAC0BIHJEgeesK6uwF4RHsVVGw8xObxjcVgwQxLjJTkjqclFxgja7oE-SzRDCMvq6pS30M5o6o7Qxu6tl9GM0XSO_0eZamJZNyeRNnjK0ldKvZ9JwnfkePZmJPbNb-AjxPN-z_GKPeTIrFyAewo5KA_S6m1Z0CSRg8oJVbx0NWWL5QY=	{}	rule_1974928
7452823412	+923349681882	1BJWap1wBuyDmmtjKIO3P04AZbF2Y58U0fzup9mFSXo98lshnsY-nYPNvRu6gpidrnP2fU7PTslVbU3QSynKslv0QrtaGEzyBMNzJnU4ROCdBWr_jD8JeZIFQJ26c_4n89MibAEKGhmkKdchd2ZlYdqAahk6quct6BfDDkdQrsSxn0f0Cfo2JnM4pu760GdVxiQZQt1-0YiXuCsUr9wOzoMCD175aCEF2y6uheRUV1DCg3nrGmEwOQnWEUrWmKjjUp8RMUzk0FpiEGuGj3qEvzvAIWABB8QLAJTmhQfZ3Rw0vkp5OU-hVRoX5QWXol6aejHfagEJvWsIePEMr4nciZfJ8LboYjyg=	{}	rule_680791
8343538070	+918910202919	1BVtsOG8Bu00ANOdG4HjbAmg5Pe-giQTmtkVGMMYo4tAtq7xfJaxtyZfqYzkgSSTzGb--XI5EIHw4_IBzySWyJoGlRuYK5DdWojM_FoNrT5bfBkM5qaP6TGXnzsnsmXfsOqZH4G6vkZanW5uaok1G4nzQKsElrXkKrc5IkBBFMWTEZWIgc35vSwBWaxEaNsy0Evix7GD_KfgCI6_NXnVRIFnbuhGd1fAaH_cuj64Dt3dfnRtzYnqiUg-NC2ppZKvQARlpJdrd7vOc_Mb81H5tT_fCZeQdfQ2rjjQqJTrMqxmuOT_T69X-4_v7hi2te8IdK9jOEGenzUAlm7cnoOw2dJf13oHuAWM=	{}	rule_2012416
5902304687	+919142855833	1BVtsOIEBu0wa0tGsVNuvnix4c2Yeo6p4BJ9zLKJAR0mYzAziD6a89T0P2GkUsHzWaRs6yyuNihQdbgFrgHkh4VDhrZFiex2vs2fNfuOUe9RXMgjt1pBNpX74hAHhzJ5zoX9EILSOFTRQEp-0MwCbqbfWF3dhiaUMCUJ7440-z0UXPt10RBJLPOSjvkLpT0AUih9TiWBKbi3kWgDF1N7GXVjdpMM8vbsJdVIi7EqIxTNVxusagPYon3cqTtxaYTDWUIIX7Yijq24EO_3wyEc2Poz9bcLCLFdNnsY-sxmWYmSaX5h-Z3VOQCKZJBc7x9FivZDPjDutqyv9rBcDfGYJxYmND4O75XY=	{}	rule_2154230
5387866919	+5581991188020	1AZWarzMBuxNhpNZLudNkruGzMoR8vgBtRYkk-UHAJ3MHA3GD09AL0uoyR05NWh-XZZSZoo7vJuA5KZF0uVqqWsM6Cqo5NiGwXXHVERQgoGZfJMtxMJWOolYlP26oEkuO6vBvBRsbcsnZmwdLURdGnsbgIX0DtkYM52j0XDrwN5KjzL55ynb2cWgeLm28cVWcZei-i7WbDagTSZaidxIcL3wT7LsZEuFYK-HfTW-m8pkU4FXphZbimP7tSPT5bkhGMecZnW4CEQfpgSP_Megyhz-5kcSKWGskGSXAhDby72Py4F1ekk5C2d2oAwyRhypOcSaK4lYPYb2hzxSceSxB6swjSjivxwk=	{}	rule_2089341
8127040286	+8801752990183	1BVtsOIEBuxLeP33040BLQ8LO7Dze1nRnxsJoS2wcomiPAbTyUclAdkRsuRJ_HHYIeXLex7KJ44yH2IfbO6PVFDweDko22k-VfDe1L6HKyeKEbTYbF_hJ7Qv7qmwlDVnuVM6CXHhwMNrMQVxIFrfCzAokmVz8YK5zQyZU78-s9HsclMYP7o2AZEsuXqiA6Hsp_6Kp62nYooTCfqM8JQEe5cBoX68EUTRVsfpnjMkXWa-kawzpkwRp0efPTWRyW65wCol6MWVOYbNK8iuhtS7haCJihD9x4M3_jKEZQCYTJS_0zzjoShfoXqaIy2J3ILzQrkaIX-Qkq8RL-bOVMA_TY8WLUbA63-I=	{}	rule_2161171
5891568590	+918077531193	1BVtsOLQBu6pCVPGOQb5svNKa6nOpWvT76x9o49IqlXbs_7XRsNx4INlylA8aq93--FAKEvXr94iQ-3th1Wy1-_szeYctTimPrJbTY3NNhgzTCOAuMbud4WvB2SWz1kz8hoNCHO3hgj932XcOunq5umepwcP_mU0M-zLQ_ukfpkyjhAW5Oc1wHu79gHB9g76s6QBa6_QVH47EtxdFKHuJifqaBdMyrHq8UgznnopU7OhkGvWSe4t80XcSpRe4PsZZ8-kEmjtBxc7Xv8O5xf5r0C4dsSglso9Fnh5VX3NbVbuQXPgUyXvSVf06-Vp1Y5vCbezBRlQXq9ESKfkQZl-GPwPIeVHXIMo=	{}	rule_1616422
762265169	+201021001151	1BJWap1sBu1DOSuuBvZSa--5fjhfGwku5ZYmGbkVpsq9YxuQhrT6wI6ckcdfMgZHPOPmdl3vA-uBH-uMS80CxFGgrMQmyrf9YfiwOSQgl8_Dv_eApw9FyaS9WgcKtiwm8Enp_zIxSsUgAmnZIDcz6aIylYNtpBHcj0FxSG9jNJR4DeyIuJr74Sw8aPEigQYToWfIGk-DW2N4IRJAkqT3Iq_s5NedJm7RpfsclcI6F1dzuA_65PHhMZA3Y2vOqvftg28KkXbu12TQnEAuC4l-5HLS0z4Si-xwFtLkOTA1KCfDi01tGS-5bEBI-sjdOI5d1ShUtkCJsde2Y-ujVQAIuQSKMPZzL-Rc=	{}	rule_2293294
6477484866	+201207929340	1BJWap1sBuyY1g2lnNjzPgiuhj2UnznrSLw8zNNtJSS7Pqk7FGX3srmNylsMoj15VZubsi77V9jazyAmrKfqXxfNTuCVF9vPHNz4tnux4d5xEY8USfTTO3ScsjEmT-rL4NTdcLels9x4-hgueWKmTQmJaK2PGZ5gATgbOj9kEnlWE1zx63oTk5okyjwSmrwDg5cUL7_R_Mq-iz4kceM5s8VG2dQRkmDD7tCMmcfNpvQrbWcFf4zoZZ7s2bGEr6yWtw2WVArotpfr1K5il6xzrmR-OEBlU08pLCnTibP_vbL_0lrzyQKjfSyrPMD-Vn-AB4vxftgNAFYq3GfF2X7Aw26J0rj_GnFw=	{}	rule_2294630
8224373261	+919874119311	1BVtsOIEBuzdQAFabZ_LjTmF8c6M1GV0O2Z5cc285kJA3DIxPlb5ReXSeVojJaOKjYqfXQAV-rXMVLZSwGgkyBLRzKhypqBNuHy9Ne2UNOtc8ZMSWFvbSY0XCJQBxDXlCC5kXsIz74Q9SIE115raCYj_XwqILlZJ0Xxs275xvIHtajuVhoc2NWul3wkJGRaTWxsgnULaMNPJXgn8vveMOn_kCzcKcimfkC0heo9WAd8W0SJl8nf3L3AAVkCXPZICth9M4cly8t5haUWn_NQg64IocDAx5cl3x89GHJPPWqKQI6PcoksRA4kUeJzTLw0KEfSoFlw_RY3dAO6J3w12NC5bWpd538jo=	{}	rule_2322233
5023503076	+14387934836	1AZWarzkBu1B7LHabeVzrWPMWpD-O0eGMQcGAKNfoyDROXU466Kqw0ExPzFsZzlUKt54XjtAwPZkPSQQOyvVYMvoYQTLMbCUer6mTZbD0VnoZc4yXaYgbJXcw5FnuCaT8k_2fVbwEGzUv-ShVwLm1dTuQfi7jK_N7lLmOCMT3oxYjqaVaJ0EyzoOqoim16W07prjeV2pE643sA1OIjAW4GrGn4Y6okrDbSjSO7QqpmATryBn-8kN4FGcTQ2xgxrYl90CdGIiShgHxg-X9V9tWSjvz5oyHCfQ4gPZIsH-xBpC9rqb2BlBhWxXJrWj_Nuwj3q1WQAuRsvEP5WYUTnvEWnh8iF9iK_E=	{}	rule_2663138
8006768154	+919241967602	1BVtsOIEBu1uVMTI85qmm6RTuahg17ym0QzMesVFRrySLb0k3HbWYbB1lF0w37XhSwUzrmxKMFFepOIM3xKbuRZoz8VyMqTIeqEqlbMX9Hv_rCbu_0qLwJx3VZUtdiNN5IVDrvizvmAHi7SOkhAKvtpsyMdsJ976EkEEEojJJuvDh5b_pbB5_YzbAnRqFlfKTpTmTF0JmTjj25rmFGL0fMobGDjOPwVYD316DJ51Sq2xC8C4uTyzuV30R3sq9WeCJ4M27DKD5q5fVfOxe9ouqqLerLgkQy0hSDp--5aGa8oZTeG-6SSxFBZQnua7ajVUv5Nykbynh4lqrVC_wSa4uHEDK7vSRX3k=	{}	rule_2189350
6529663543	+919635019871	1BVtsOJ0Bu8JpHM3B18HfRb6tBXs3lSG2Ph4TW3QpivcxED8W23J53d5jIz1woKkpmF93ckeRdNE3ArZoIa9QTSb3eeYhTOiyuCqDWlm5aQIyofQ3UaQgIQXbILlPJ7S_bLjbmTQHs9mtegb92P1uKZS3DvhBKh54NDmu5dN96a37UXOhdzVqct6sqal99c6LSkXLPThJku6wK3V6pPdt4WDMhjOjSkfzFuYPwPQ-uehuIS7gs7J7OWrRnPKRNKFU0LqGSTZ2sYZeKO8SObUz8ZV3PnJyW4ikkElSLfpT4oLkgvN8SZFiotOqxfJdGTJYB3iBWykZ9DanznM_8hytji4BN3hdP0w=	{}	rule_2978426
5406442663	+68987274925	1AZWarzcBu1SD94Vp-f2KlL9N1YtHZCUrpqs4BwM1kKK7vOr6169MKyedOZWZfqGEYsqlvObu-yRtOjqZ2FTw_Cfr9XHB59zH2CkTOHdPpQC_Huei2vW3WGRMKs1xno2EFdZ9B3Xlu7H-Qfop_YG5HUz63xyOdlXfAO-pS_ADWGcI14lj1fQTf1zpos99dT-XIHghKbUYUZ2wwJi9oC-uvtLEIN2yFi-oTNq9XMvIuLxOOaC1BvvHr7qMof6TMdW-f1LxR3DMSsK-GEHxrILky50VHwg7v887Z39hn5KifM8urUrJQYaClqMI70UrGQuv3dGe4RhvWzNJQIJdQu7dBueNYmBTf6k=	{}	rule_362648
7669122337	+252634016865	1BJWap1sBu09UZJBIVS4MIvh7HFEiqg1onTr1s2jje_V-WFLQDQ18mcDatQ4-jyTJgiuGyDjc8Del4XMW89Y3IPwUVubJD413m1Go8pthma_rw2sbnakDy2kdl-14GwdPi67iQLYlMKjfoc9GzU7YVy8NX3zimTjHlHlDUl2AHH_jSZCXld19cHjOgn3xMJX3p9ZzKnyU028ferWuj6ucSvl3xxdWVs3i2LKdPfHHqW03WHrkKIUBfHb618_FRE-auWKmzOG7Bb4arJvhDZdlgYYW5JcSKr02A2N6C_7cwbTSfHt4FeZMOhpUthI75bqCNl0tTP5Yli7tJZmj7L6X8H38czRC7A8=	{}	rule_2488327
8127965483	+4917674041234	1ApWapzMBu33ZdJEk7zaI5hGOqriV4c5FtrwuJ9ao43vslW9GJSGkzbwPVz-lmjFHVYpRBO5HPdqrvgkeFd9S_TbI-Oow9KwYxeRX_wV80vzHKN7wmHhI8i4hBnNcAyiekRRzTwgCllUqnRD3qqsU3MqAJPyHeqjQd8jSRPxz2aH5ButkYv9TMZyHxQCPNcriPcg4nDeuk37MaxdKfDgIxtKtMYZuCHtx4revwOweA-ZuTewAd6C0VFvscSxkZebANFKV8tQmVB8WeKwA1GqGrXSW5aB_0bUd_8V1ldmmFQnreCrKHIgyaFDuIDkuTRP54_vfXsuThM_Rgm1Ffdd2zZ5KtNHJZns=	{}	rule_3147250
6087538623	+919452316311	1BVtsOI0BuwJvYiQN8sCGjqcTy1QjPCyv6ZOQoG5WxwcFAPzzRkwtmfB3rrWSKUjFUb9V368ZtLwbAPgnw6p30sGsEVHde9sIObhiR1Z9ANKKCo-9U7PooaKugv5Szvn12F7fhHynutK8JJfIRfV1uMAGlRwq-YhObqLvNFCezU2qNU5Wezeuov_MsXz8e1iLICL7AyasGXWN-NdLU2crUyStnoWCS9dndTUzkuE3GXmw-uf0-okT_n-yjh27_FkPtdRAgBYuz_vFY7IRpcyU8hzZ4SjIbbgOV9NHt_lpNkJEzeA_UG4DVY3oR7oQZ4RyKubStmwiawQ1KvYRYFM-B9jFbr6MU0U=	{}	rule_1894044
6636475980	+917597828427	1BVtsOJ0Bu6EmXU7lZ2EUwUo9QxmC5fRqI46utO18JAH4OLHPh7cQGsapa_kVx0NKwzllCjypkbbm8S-rLarlgnQWF-2fsx72vzTjSgL6ske3p4_hofmt80fEPrOqSOC7KLaMgmbBkA7wTFBh10NsHADw-A-0L0uoA-4miqEHlJCVwZ6dTOkHLy3Cakvw37SebiwtwBHBX4JMxsaZoU9YLLy2YBx4eRWuLzz51W9VJJpDHFXxQU7iht1wjAbrd3DqxGU3UI1qBIa1CuaCV1HJXibqG6YZF_tcB8nVJiXID977dvKZChugDpiLQRQ_OlmIHI0xRWSjai-G6sfZMj03IAsH1IbNXik=	{}	default
5750203191	+919305060551	1BVtsOJ0Bu73PYYTCInzT82QAS628kcOQ1paLMGdY5WrCwW8K2dSeBA29cpGHK3QmVWX5-eHtPNcxaHB2VGlrYrry2wTXbqfHr7PkKFmKziUW4k6DPf0uftkqA7-AiEvodjz8u6wdjYrjC4RWIWSSk4gYwMCa0kjQSCe8Gz0FAyhsjPEWBosvXs-Pg-G8GArTU_K_KaA_49nSGVLjNNCVccnS-G88uQBzE7yKqSzR67yxPqDTgoX9HpcK0NMqa93479_2ybZcwoADmNxUm-EZlNM1FWnK_XaeZVeK2G9v2StlcXHt1WVnHcShqacFmyYbTRVtS90xpQID7XYxx9QL9FK8X9avZvA=	{}	rule_2907119
8126606818	+919476580728	1BVtsOLQBuxwOwvNSpBlt1JQzYL0vnGgNxs3Pe1xGCRWKSwc9iICZuQSeZiPRAbR9-PWe6fQ5vSMptuHy1CJ-C76yk9B6Bfyh_f2SPklSp-3l9bEmhoU1Nu_zRP2IUnmxxfrjaj4h5w6jJ7cj3LzYws_KCZ2_kfHDNpV9cnoXPwXsbms0FTtiZhvIO4gr26_DG8wQCw-MZjE5ZCBvHf3YExNeoHb7iobx5TvM4wG_2Q4gdjmEVs1-6dQ_2INpqE8HEqrXFqFWnKsAFFHbYcsBZupBuSjGfIqy9SQqJZxu-ZdEtfrEEK7o4oKsICIs57_LDQVAWMpUC9m5Cq5gf_zd_-ruwUb_hEc=	{}	rule_2754801
8012257232	+923214229150	1BJWap1wBuwEJbwuowzZGmZTSBYCErpgSKIQ0dSulSCp95f9p4dv1dlbI9iU0ZsQML5vTcCFCqO1UJvSVSZluo3sNNClfmiBqOUUUVDsBYsk4Eoq7j-_L-T5vxcxYy1siezuqIB-PXYurvs7y6KB4cYo-uCK3AR2812uzSu8yPtQixV47ex0datEtmxcrjVhBaJBLO9QKvfb-v_qmCnG3b2Ya19YzD7oxFZvF25OeLh_NihjdwZc6CAIa9j_rD6I6vFAT7qb4kziWHf01B9p6EauvaGE3JWaVuudJmN2NTcNolhbj9oWD6yihZudrqtpY3MOBEE1EENWJqMYqnJ4XbBfvJ_sNx3Q=	{}	rule_2817684
5821665830	+919405256144	1BVtsOJ0BuyXRfVT5kGnbV23RVpQV3dfJcujEJIh6dxu5jr6ii4pkf29C7UifC-IN6wqecVt11E8E9ja1VNy2wE3Oq7LYZzleQcMzVOV9mNoEzeOxgT35xj9etXUJAiGQ2NHEIg9_RgZMsFHd0PA9C4LrDgMAz0sAajwzXY57TeM-PkKPFkq99kyjD1EeSWKF7cBzzjewAEkTNR_j6SdsN6RsVZvBTHFSbMwdIlVmKFxjSu7fME_kz1slocsEQJ9DnbCZ_WzePpVLreRfZkxGNPgh3ZQbrcVcavY1AMpvGI_eHJ2wYCYKuftVNvqvIOIB9T3Rk4Y7yamhxjI-_AAzZyCJAG5J0Us=	{}	rule_2922360
6490654709	+94721499700	1BVtsOJ0Bux6F9_zN3WBe0ajtfiKfblSVI41AxOFZXbRzW7Upo18y4X6WQG1sOqzasT7i8qSIaWABGPbDlZdMdrr3EAcmbBvmtm4HCxIXLON1mej76e9Ip5s5egtBW4YU6ZmG3tBoYTd59ydDvUPnTgj-JAks8jSPsiPuQlfrxBoCbgummLVvqfivlnM41CDr-2GxHIS2ueLBjVqV9sHt2WBOJ9ZV6HNApGd8O3qnAlQfr8YeIpzYQkqhhInoRVbvsJZteDhkxt0aRTWiGlLfejkcHKlHa1srJTKtb-Brjc2U3xjEEpgAgXtOxhawA-Da4N5D_oHWGzVqC3MWMQSSB3xah4UcXSM=	{}	rule_3000381
7786809003	+252634016865	1BJWap1wBu0e33C5Ug-fMWhku4Zcpy5FXgu77IitQwnOWeO8M2Q9bxWqr731sxC5KzXhpJ-fUbXTHOf5loUfAZSb4q1-tDl5Y3ogvSoV7ssV8pB8CxoJduLyvGPrDrMrY6NJo3qdY7sDbxIk9Cdc6FjKwutqcpPxQoiy_8goAe_5uT1aKJsljILI8hhUNhwlToeQ-uMXQmseWE0LVEK8IlDvRMKmsyrwd3AWCtY0okujwM7BC9mb9MH_SQa0QrH7DNqqU9eqzbk0gphvvZ0ktU9EZyj3GOcTbj3f-arlgcj8L798iJctcykBD8XTmc6WWUA1PLjw7AukEyntThQul0X94HUzKTks=	{}	rule_242682
7693672756	+919311530449	1BVtsOMYBu3_3LuEjdHQnhyCA-eJX6TlQOk_55RhtNmfBCjs54ZnUfCmojYQnfKh6S63w0gwSdBKcnMb6yEVr584jbXJBdbvdySLud2aPQWN-BqW1MkisDh-gdKHlgCvjKQSd4G2tSmmrnVlyKB-YadCP2-031UhIbhHmUKrNJcN8_Y6VPBzD3UUGJUSuC-_zFsPpEMBKFFhMXHa2_DTy6HAdd4hvcM1IqISUGA37jsPkrkSfinY7FzVgaEngopLtaIAi-AvlldnPWW2wefVOTpmijr-du_M7d8KAteV4mPeBWQhqFcbQOhC2mgbzup57mFC7lrljZAm-roBhfAolyuU3qElXQQI=	{}	rule_3251577
7903348966	+17799779382	1BJWap1wBu02zdB26ZLSgSHzq2RomX-qgOc5OlPkBVNUJ405O8J4-Mu8AyOHNgQJGMB58ekmg_VaUBmMGf4WH7NN_9KhlpskRRwkO55OTZk1DtvHM_dcfWNPN1Dswx4drwRp7cddRy9Lih_s9NXkVWtY3pTcRjr5654J52YXemOUG_pXi25aLpJQhX3S7vbXRxu9V1rtnwO9mgqqP6y7Rsx6qYRXXPK7JB2IYYyatUAHgj6Q0MQu8sPJrD1yce3qiv3ryn5WE8EA4uMlX0dWfipDRl4RG1nMtTkJEo7wlFS7X1z781Mxc5rpRKxaZu0OrGZ33xzfxthGRk1x6mHFNH_iQw4eclYs=	{}	rule_3046200
7433900109	+919875663110	1BVtsOMYBu0rZsvn87t_IbBN1DOYWi1qgA4eP8RPwfYLkoXWUHMWEyooqJxge45nFNE6Lt-L295uiQbIArtxGPguit1thYrHstMVrwhGx97blfzbdNhvXDAChsqNTU4D8oOsOygZ80ylau9gNPhhN285j_OED953evV9lNFzRCOdUk9xI-bu6DovEtik5SWYrBq5NJylUuUGUlbB3OONw0-TdhLZX4iqoKUdD_X95_uuqaaFlzQ8IZBdmJgHQihbG2EfhjPl1vfJRYz18_r3GWnra1-MkwIh8h6GiaOgBACwdc90cvXdnT6hY_PUF2ZLfO_f0kbCUhyoxkJlmqk81Yp4_GQg-8hM=	{}	rule_3139397
5848770400	+971547088866	1BJWap1wBuzy2UcY0dNuI7wETKl8eTaX5v4tJ4cExSSflKROZEN7HFxY-wNpkpiFTXzVqm14x9dHSeozdFmGMBVA1uz9AUfXTHjUiZU9R6Zh23jgC_qoQsc2cFcMptP4pmBwxJlPfv7WEdVTQJpcOpKiVY7n1W8IQ8LaLP5bjoYwsfsWSTr0iKJ1SG3dfWzjjDLlW7rAjS5c1XxnWUsKCf1TCJJCIGyOxdFZBksR7cwC9cvqcm0XtAeFvIp5ETsmm24gfnK5az9ZCd4fYlfDf0UPSiH3ZUoamkNVmC-5RYWkrSHAaJb40zzMguCmWAhML8cGu3Jkj8XiaMn8vBBx2w9lx_PHV7mI=	{}	rule_3252653
8323818787	+61458476211	1BVtsOMYBu4Fe_jNzq7XxdkLSxv-dTIAvVj-AuOPF96uSuU_c-888OVGEasN8iYNYqYXrabYXVXjyyXDrkE8BGXUA2mZcj29W2DeFUiWZklXy0Z45qPI60fYSMDYKdzhGvMQAvyeuh7HbZKctEzFPc2TysbSu13kBeSczEw-M53hDMpX6Lcni8SfzsK-l0jda8J8jDKZO3knLoIkEPdzzYDpTy4_IBgMzuy7PYYRZmsPx4dZi9lRFk1RmsswT_zFY9D5_g4weSU4jLOUmU3jPBmJepPPIIG0OlimnuuZYGdQMrvD32vF4oUfJJCm87Rx-8YV92n2ayKYDPgZ8dIls0sC4GHP6scI=	{}	rule_3146502
5748157494	+919057502048	1BVtsOMYBu6EMvd9WcjJh4EAQ1AkIedxpgbTNo5jW3k4UkD0apMnjYi8nsBRQ2MRs53YGq5WZD9nNIh9D-Fjw-htqgYGPbcPA50cS6uuSMS_Eeg-q66i2bcF9np3jxZiuUwCuOkfYzjYzrbMjHSRc7HpjAHWIgeVluXswdzZIrgXDMQ2-5QRQisaK5MA4YO9yPFfXOCQFe_ENAmbLcv75-ewOj58jhKny3NokT7o_d7h4smYrurs8VUdQJaAKON6mRjmaFwb3so7CzKwAEcBRkMccGYNJgM8bjlAvzhZyiESl5gfx57a4nd4EWrFqJnBLxgyAOMwbo-1hPAILJ5TRDFLpgQ0ZQV0=	{}	rule_3149973
8370995918	+917778857087	1BVtsOMYBuxYj8oDAvWcRKd9Zk-foQjOHCtIYoGFrwq-HB8keB5KTSbhleZHIuTo6H6NlByLvOcziPLxIyYcErP8eUKfYIQTb8e8PMhjX8Vt4dFohQ0hIU2EN_VqKbcauiEuHrKmEGAETopST76KuL8ct9C0tT8nbspbAR5Yj-MDSGTgOVrBXk4ImXgZpPyauO7qt-SXWISfBtFQeneUFvPQdONe0cjGAhnP6_MUAo1qo9TFITFOKboXTMPcV_9Jm7aha-YVPTKVAIQjnnHN-gXeDxgvV5b5ky1jJ1JdVjkLDEFC3n8WLRcquuWfvqAkYF2l-8icnOQxr13q6yRYmqK8slV5Mrqw=	{}	rule_3186888
276419595	+919560023125	1BVtsOJgBu5my5hPAbDcE48BFuF1aZNMj62vrPWVd1H9_IFcKYjmg5Ytr9Kc-FGmZ6V7fcVZdBzkRvZprdG0b0_PwX5oW1gEvI0nRSzprKPjt3-0Ypukufl4fdztd0C90OFvh1sJm-J17Ljv2OC9BQV1pbkw3qr9dwg5FzZBX9skaNrfYTwAG6rsE1GW7nmnIFrRvuZpPPFi6xs4ulUViW0N8nSpYq7LOonPzV4I1VMqgEdANoyKcEqHCcG9LL9i3t_YLP0rBcRYwhEzKkZtkl3v2o9irRh15DbxoToj8gbBJLUU6GL5_g92yL8reBuuG__LFsZJn6M4RkRf0lZWNv8oHNBaev80=	{}	rule_3404108
6331543504	+919006169806	1BVtsOMYBuxhmtQTdIFJNWLLDZZEYJU9nDmZvTyYx4df6W4YJRZz-tWlG4qV8dJIMLyUDjLGPcWjqjypI3wp9BssNTiwW4HJ7rq5dPuMsQSgsKUl1L47F8MIafDhqj3SA9za-oaz6pdO74K4Xdzg1lH3VlXJreaeBs9ZHlFTCyEh-fxHpml0qus2ZC5wgsojSwBJnmQACwYnZCxX2czIk4Lb8twZE67XMC5uGdUjgXQza8fo3EOYPcnBiKgddYgUY-j6zKzOuee2syTpfw1_FaMdaYhKD7lh1rckvOGVll5Jt8FZdoq1CaKohi3w6Qyo2B6-SCCTrOpwn19FseJsxXMnrE4c3bWQ=	{}	rule_1334118
5921486522	+252637044133	1BJWap1sBu6JFJW0IY2LyDZfR0ZUwdWMm_GwDrvBy8vtJpXPJQMbabAtJ63VlPZzuGXlcRkTd8wbsOR3xTpjG3icgd2SyWFDzrVpY1H_sRSIRmhtsDfJ-XlVge9dHx9GdSPeoiCbAoSEzM1xePcckda5qKiAHF72D2tWBo3RoW_GIYbNjnE4q5bxp1PzWB2uxjTXsvI8Wo9z1BLk0g4XvB94YkjBzrhVPltxc7mzfAzbgWjd1HUWG5rce2xzAQ3GS8bWmL2pXBeKCMEoUTk8jCQTa3eJQ1BuYvWEH-uyneBGov5hlsR3l_VgFUfAkxdkoF1Xg6Tb_oX5SGaPd3JQIk-m5BWl6V-c=	{}	rule_3413369
8460919996	+15408619946	1AZWarzUBu7Kg5-i4K9j-96aZRer4OgX8hEMo0-mviozhGcMqC3yr2tKxlDtRljNmdrl_-zX8dVEDgPLXxudhN5VG99DCe6l7b-yo7tsWg2NQB0SsaTI6IYjSL6vEQMJ5FJJzZC6RZPCcgIDZ2O2zA-3NzF-eUWPdhmBIx3Fg8sQHcwoDAHo_Kc_KIUBkQjSQoFeYa9GMHE-BcTsjEToOWgtL-guHVXRwzs3JzFwipU__7t5jfOb3elo0843ry1rEdxrAkf9IY3R8s2BJUGnykjmAJZx1PxBji3Q7JUyIVZwKNtahjoJGYloeH1SRZmzWWwIX3jlx3WnMSWr-F-M7LhRJubp7_2s=	{}	default
6636522096	+84982342674	1BVtsOIwBu0jYupbSNEXNpnA6NOUIDHbDooEhshZ_Y9cEQckd4vA9svGooLCMWp8Cj_emqTjkab78KHE3y_rnFot931xsUSgYTVb32uydz7Z9gz_vbocul-MKH0_Qh_i7ADAaqanBwSrDt8IiGoAVQpdBtD1ssNMLQQ5yGBlm9oh4SvxR8f6GwQQMbdX40BHfoUlarq_D3kn6TAGPKaGU1aJrc2uVt_nIQ1aR1lpYwYfVz4Ko5JRnip4Y4p-PKrcoDcmcpp42UMj2-pBAlQze5XhrPcmHXnoMmZP2Elrhz6oJ-UnidJj19RSeW8gLSsFvtRP8t3pdJykrN_II8iUN2gmvXWHWtyw=	{}	rule_3487339
7209556360	+8801969128531	1BVtsOK4Bux5rPq5JimZxrikickix6S2FjNwWAcGoSAojM5tqzNdtF-uedhNTN2XB0JSm_LY6uiUeU2pbdAxNv-dQ_a-6yLCcpoTBy3WOs6LlyZmcMz7mtcyziW7m_MlWrtZauXIdqQHjdXhmHAOov-_va7HzvEw-UFxrOnUWN7ZGXQmDmVtTPgHL_aa8xE7jHY8gS1R1IoQdo_d9jHFcfVOtQ00Ct1JiKzLNn7p2Ed5MCvM1jtDY05ZJsXW0hfK9UQHumnP_dYWyGBxDkwQoM3lpxhrcYlmDnAjl3IvW5S5XiIdAEPYE5NnxYh0Kmr9SlGcTiZJa8ICvQHVmBdYoW84mUXHHGcU=	{}	rule_3452808
6830041427	+919735692378	1BVtsOIwBuyVQFQLzgNO7tnHQA3PlH8sEswHc5n3dz5a6ao84WipC_8gVrYLiSFh_6zDdU7aVIUg1ECCY4ll4qm_SwbGdDeSdrFs1MWdGgmrBxGHpQNfThtdzGfg9ZZWAQqWPUC512IooHW4B79J5wRN04wKfaPDk-bplgIPKSENXMxhqtjthP0V4KG_TBhuWgjTjM6UxjDi3utJysPr9XEyxZ4b8lojtRRFVn6HWdFwhewSUoeUvQLVcpvjLjeiWAjTRBgU-HAi4HvMirHwP3qnXQVf0PtYqn9fAKoyIspCy48pRDi2OSOZS2xizeOhj_cINXvaR_AuXn2sfO0o2VfoAPmCTjdE=	{}	rule_3506946
7488381628	+917068297381	1BVtsOHMBu3nlkzuxAclpOcaL4ywxDbGT8YwzrrbI5Rr5suk6ThZpzKN5jEMuwg4Vrx3oNBmsk0JVKk7_DtGDdGS5ecBnx6yghS_dOOuxw5WnCYfu80-4uXJZlq2DvT7ktuPa2jTsXe1GZD0GBjkFcPX5XRLUm9PINOahqbuzj56q-7JRGh90KghRum7XeQF8itciASSM5Or16GPlU9LFm0MQdTtn5QSfVKPL0X-qlR2LGqIXC-7c6QzJqICPblxLe2f0qEU5uAlCuqH2YbtmPjOM-B_Wrnku0pqiVDBjJupFctI4JhqgWoVXJfrJLuNSH0nXGfFmQyRT_Za4o797X6YbhGWO9Ys=	{}	rule_3517161
7431619619	+918757911119	1BVtsOHMBu0-pC1OxlLot0VeBr5fQDGKubO7cbp6gvrHSwjbYIPeBqWfvx0uYE27IZ4J5np-lLpGB9rmxPuIatgQgXhAnqSiQjQZmirHQUnrpZDprmHwCeQd9JFK2FpauV3ndZwDnmsufOjibL_b3XjpibL2WF5eKDxvWgqQks1Z1ofTXZ_A1MP6Sg6DYyY4wzCsixMh_cnFTMBj6JdCfS1zD-sD8l6aqtLkUW4UOXiwDvCiGn5a2yKFTvMseA8Twaszjd7s1yy_LzmSVpHag3ybdeiKucU1NwvQmPHn17uZvsnyTux2YGQo0FnsNNeGLYoFi0O7pLpvVnSNiacuKDrpfTvgpJFU=	{}	rule_3599845
7796576246	+19082673117	1AZWarzgBu0QfurFUhVyAW-mduvqhdb1d1IB2OcQHvjLQ-qt3eI2hTxTyqLTFZng0ix8dlI1WTkJARx9mdHKq9XLiBQCFtsuTgUCz4VixFKuVBZ4tIG4zwHNyZCNAW9YqtlzP_pY-kqIHnOwDplcS2PBAdbdFaMkpCdu9LHwvJ7cVcS3_MEUl5gK01qgvb4f5Qlywhf4nLGAhQyDxwNxVHUayK1MpJVyQvJy8W2nPHM2EcPrOhwPI8WvVU8M3-kHN1rR4ft0VhFaJUSkgxveIxpI4aBMpOy1X0V91dxeWZ6t5ZcYccX-e53sXTz3XIkTkk4dHS9JJvGlt0ARzCLCAoOrPWigKtzM=	{}	rule_3623961
7258034641	+998947964131	1ApWapzMBuywBY5H6XxziVh_rJUQjtt85Q_NBclGYMNjVWEwyQsaOAyIdP_0qomo-9KF7oC8SH13CQ-MfT5OppDVnXh5Q92BXwxn2C_Yhyi3JKZIfx1z2Xj6YPu-9Op2mdMAyqeX-6mzjmsA3ZsOPzlp71BCpQbt5FOvwIxwQM11NpFVRbNf8WBXQIkYhql0L_1ym3ZliB0pgxL_0zxY03m8D4hL6pG7e20u7sKJL--RkucpNFXubz8ogQkHgkM5akFliQRmK4Rn8U1-jO5ph2o24Wpfa8rYU9PboSVQ-1uJ7EkZVU7IP3tI8GiepTvg7kYmJgOQehUyw4rmBQwv-IrJF0ZiKlIg=	{}	default
5389796957	+4917632719165	1ApWapzMBu7dfYD0r_PycjJcSh3sMTdtNkbX9_qfEixwjLzknL0g-kYA6fGESigbsix6Xl9LE_FvSp_hLAC8HauxT0J0UidmdpUn3UQG-5gzTSAE8K9N_kE8ye1qmDWELD8lsmCz1iyaij3VKQ-desOVo5puYPT4afYIOuDL4I8vhP4CO6QDFFtROfHU_DxWI6D72rkhacCCeGtRc9MSD58Fi8uwTdQo8JYUkmb8GF0b725nU-SAFUxs0CSVkD8pzdc6Qn_uGAwpGvgfKo8vQjqNtwx1IemjAA4menAP5tVKXMcFzH1EHZS_6-zwvL4la8EkeJs4uHJDFgoiSD-bVKtEvBlqOGlU=	{}	rule_3607326
8069225688	+919837546162	1BVtsOHMBu7E69kkvYpCLsrgs7mO6BNlK31l2p702uAlyn-JZyZTCTMPMKo_w8lPPAX_0nbLmQpZ9SBE6a4F7f2mrWgmE4ARlEkxYfaHS0CAuZBqxdqw7txpEZq69jTcSwYU9lsFpHMUULf57tDHW8wHtLXfVaoHUC-avOyCg1GkvoY1ZZAgRMpv4rMmdi6BLE1RnM9mBHrh-AyoZA7AYrzv0Z55XoePV_bYy8mw3d9MeFUSuYI8-KNDpTGQnstN1SnMa17xN_o2n-nMEU5F-pX6-fhgpR1J-z2-A_kjx-B4haSVz6DxMNkUGY-QLkOIWRlyTqAAoifzrmRHnMY6wAcmdaVNsWM8=	{}	rule_3675538
7582960557	+918477974007	1BVtsOHMBu3bgLsv8B5duqMevLrpCOPgaAF4RvnXAgmoCLSTUXh_KWHE6VDYZMBxQSM-TJLvVtf0M3iHpwjd8F8dT2KOQae6QsaIJIUe5x1n0riITxQrhk68yQYuXGXiaUMNEFGwjqPEKHPlzUhhp5DIbVBWSBnmCOor4vA8nyJpRnIJuUYEKvFBmz4GRz1U8XLKYlNu9VrXCGy7nhrdX58tnF3YF1WCmUFdr_BOfwv5yjjZgMkF0jImT_bP_IKAY2whaMdpHSbb_v0_vG-R68A5n1eAZKSVVFzSo1M80NFe62ZJoqTtCw_RMcgLR7anNUuiI4R5bexNUn34ApwV9VPaJZyzh8tE=	{}	rule_3675804
5332226638	+919052180914	1BVtsOHMBu1KstqWciSq-ABZZD89qMLKxwh2tKUaIsldsY__AG6cNw7Fnmv2L6JoA8KcePRS8C51du6d9rz229oGo-BhuZkxyoxnKDWmkjJYNSxjGBP--8F1GqPB4R5inB2fgLyADLVDIZWYvoUsTzMF7GkeKfD6PqlGdoHsV-TO6WE8Ck3U-O4RjZ3hhnonurZxIIMIIWLFzyR1B32rCvbmc3Nl9RECyepJ7EK3De8JYNtPCzhS2tO9jWcLtMqOwbiPzuu8RUOP--cqx2X_QOw1QWcmtqHA7RBMIuOk0dKSgxiJ1iVmu3FmGvAVAfbJfKH4XUBK0-wMKLr04u1DIuO1AI12VXs8=	{}	rule_3699972
723189008	+918780113898	1BVtsOHMBu0coX8BBAHuWv9AB3oQxcUQ1AGFDZxviYp7a90k2VitqpHbHLdUVGQfMqxx3hgZWeMDoKy7KtwP4uHJLxfwHawAU3QveN0nnO3Y4hdEtlluFJklgcd0xa1OJBu5_wtzG7qiSNqd-BJ_fEMn8HwlD9wXhfPE18vmAo0vgqkW8xtYh3EzaALMF4NFZ41pTXgp6mQqwPh9TIaEfObM2_9IE5MOqOPU6gUADh4TH2ZssHBYsM48ml6HskP98GOqSTreH7E63OwkqGUMQfXBhnKH3L6V3Mr_txalHyug3qGXx2ykxFBVm9n85sltQbef-VOkSUwB38X_Js9tn6jmGgNTwG4A=	{}	rule_3733604
5451780987	+918294735721	1BVtsOHMBu2cbN1ekc3aDVIZ2i7pQ6GuTt-2O7n5OyvUwisdmvFzmLO9yB-_HWl4ftp_vNNQQMTc5PcZC2bA1xilZO13g7JlsFo8DcrG9BvYiOiqfuUuw3kdLvVkACnEubL0DYUBqhTwfvUIOtDvZEDk12WBF2VVbg3doYLQEqL3vvJLXnAdisC7RC6vHqG024AthUbymLfH1IEbvYAhk63zE8dpbwxrYqiNDd0cMxztJzmQbaZkI-gH2tkMpMeTWPJY2hyH0WjsCxNVZ4-SQj1jCH7TYfO0epczStLTPXhMex9eJ8vgFCZyT4qoGNuZNaAMDeUdsHLZwYk3neV-aEzsb2LAX66I=	{}	default
1700711970	+919981881490	1BVtsOL8BuzMS_Sfx3fFsuYm1fhb3uF4jOvfaS5poAKMKgjTUkdV28agsx2iR-lWVUB2189BW_H0-ffOtZarrShb24zTS_nD82AD4bMttTm1ApaoE--DECuUDTM9gz_eHVMUcWOLAy6DHs0KvJ1Vx2T6VLVFz9rkWCEaFXl3YpDDozRNYg6a3upvEJnWMYMcKmGIggIBKxwmAWMORRCrPDzb-IPJi8xvhzCe3-9uwZ88W_BU76iDYpDw57Faqf80jQ0hOziu_M908Dbhqtx0DmzwJkAHbjyOXSxLlnD_Ce5rwJT6m7_KRD09zr4-3-qO2Ca-LalJlrslnOGQtY2jeGYpfVW0RXN4=	{}	rule_9774
1212321102	+917654244947	1BVtsOL8Bu3KxyDkE8DWQnCABF3X5obBWMGxkA8P4pkBLwyCIIQ5WkubKqcl0ASIUQq8uav7o6jI9X2ZVWp-53jiJXKqxZERE2UE-azjIxPVTdPSV7HEbOQwEaPPQFzvMZaLPjpPSkLdjzu4hpVA_87Khfer7g31mPnOBTL2zU2zfTm_ytY3QkXiTJXCLFImgBbN1ZrzcxsdJLdJ3n7ToJJuOTcYe87RdT1shQbtJejJTxIMD4JUvkfDYzZtfUnngst4guWu91h0Pf8qFnsd2PZMU55TmXOlgzDKCTRQkF49YiKg8JjryEEPO4RyaDoA06MzgtYH7phLwOPMz-vPpU40UiGwE4ho=	{}	default
7174833388	+918447165954	1BVtsOL8Bu34JJipljBbCrLfJiITvgUplAwBU5QznYqvFuV3VKvGxFT7Krd4tCV9ze47EqLXLS1jBD-CedjSPQvmLBG_7nA65zQNBhFE_JlsoPcQEZ_12DWWugpt5onQD938rc5J7Qmh4EMuP7NiZQMEdmfTSUPFFdI7vfmQLWf_d1CjcV5k65XR_UDXioFZfLd_U17gaAifHU9AjbtkJrVDmKeav3WpVPAmtN25dI-k8XrXTX0buc8nWGSt67mMh6cE0Oy2LTkXNSp5Bn7pfsBWixpsRHAkM0NH9WdBf4MMSLOaK85DVEr7BC2jw-6URERJ2S0W1OgDsvr7gAalWcA-n7qFhGE4=	{}	rule_101659
6027932766	+919304757459	1BVtsOL8Bu4EZaH2wjtcTQtaSOjBVrBrD8tkDjorg4nQ8sMdj6bnczv7qul65E2MiBmIoN_0IefOoR_Nq7Aw0d293Guz09tz4IEVHrjhCVm5jmo51gBGV8iJCQSfxv41dUjj03V6LLVKCYbJJkf-RqTb3hY0YFru9ZC4bhxuFAxT44vA0TFtoUld8bwLq07VT0JvaNIcjYwIzubqdMr7W9nsjW-Zjds1E18WqTiRxe5FsCm7Ug3OrTQ8gpKPTu2-yav3EpGEBqtwM9A9khecj0qRZ_Yaf7mm4tGaa1waT7uCCOlEQy4zsg4XW-jPTdUgGmHIY3fbtiDCmeQzTE735Xa1mUqvJ4ro=	{}	rule_66773
8280548411	+1 2693605725	1AZWarzUBuyT36_tLSV-a3T4BMS5J9ISL1lmIAH2sBJaGWB1FeEsC_wMEcfJBTz5XEyK2RD5HnSVhmRhHIGWjakeUV-ngxz1bOJNMlNURVdxeu9lG0OnS1yk2d-Zlbpp0U4_uzjNbNLHh-3UIUFrOW2e6YOwuiyFfvf_NpYGS9oWILzzSTTh--6fSVFAOGt_Hz6d_gCW6_AadRIhLFQgwG9rDGhhimHZC2v8dFacoEH90jj-YC66772VlTUxUtd2OmcIr2DAlvK068s5ZoToSPn6UrfDdg5C87upHkjfSSmwYxn8yXAOFZTwdqygoXBcizfA6GEQMrIbChXYs3ALSE7UKP0bSCac=	{}	rule_110584
7488003312	+919229152134	1BVtsOMUBu5YPbPNsT5Zk0uZKfb1qhmqeIGNX7ofMPEyyVDI6OIpRpKkNZKds-OK2pTVkkotYF9xlBnFCzMWg6BkRp2ylGfwuXKw8vCg1H93YCZZk2an_LZ8q4EcVUDwOvI3ziieVS4m0osge9ezYSbYTJfC5P9On1WUFqjFA3yKnSx8nvdyRuMxPlQK7mr0tHk_G862zgj2fApWWuVNnUArfmLIxDsghYYPl_esT2fke5kJXD0WW1Coi7uDSWkyLzF6hTxBfsxhiUrilozGNLd7d88RjW3FrUtRA76tWPrA1JkLIi9-40xcbl85eCmlQvku1WBufYb876YcEBodNL5IgVhQ8vWI=	{}	rule_3782901
2012655294	+917461977458	1BVtsOL8Bu6xh_oPN6-HV0Eyw9iKCa-OY8bBgwJzs-3I5RBOB2pObS3HjuZfYj_pzF0nqlKhw4a6upySCH-RXmmS7lwa18AAatMkSIS_URMig2LpfQDcWcWah-4S8-HMKNWllfjSK1kriVtEbm66pV66aYpphAleqRv6kLemS80mqV_2YcE1C-cdpKcXpBJhokMP9qlstm6Ovgk_2513OVI5gSbpe5wTc3c1CCoybrpChr2sQWBQVSdcwd2Exnw1O-fB7JLH3ffE6AR5znGsx6fv0c2cDigm4kp1LnvX7SCBQNmr16GZaNHZA98KzlKvWNakKf-rhOBBZDjx4ffb98PAhIGxuB4w=	{}	rule_195606
6588828344	+919040860869	1BVtsOL8Bu2zZEI1LqH169ad3v88xGWdNWhU2trNOxnhSwBWur773zm8_Nk1z2JSI9N1CSrKYh5k1nzjv92FufN8Tf4TkdVl-Tr9bLfgQ6ec8JnF4pUXCiixf3NQde_AehoYNpPCO6hpPDG-CWmyIxBxOIsM3drq_7RHwqN8nEgD-6PMOO3onQOuS9MTSeBAa44-lCq0ZqzPV3xNTUvL6-UsuJG_Z-bDtiPC6FlugATvjivFEhyQxi7a-YXoAhrElVGA6UlRjOd9Ma0fvrbokuoeExkvWQMVTx56xC7p-5CQMBUlI86bBUrW69iNkQZIrk8uhxwtXBOo23pVUTpKGENlF1nrqygs=	{}	rule_134856
5445448223	+84343273203	1BVtsOL8Bu0yGdhJqA_u7FiJArSLnMXXNVrsVoXoxjO1tljvjWr7CuqAD27aJvT7DL3lX3YT7h5YCI88ge0WAPfW8OUlv5DHzeQhPnZ0fKAX7T997IPi1-1REix45ifdRecXu_3mKAVYsNbH7RkGSgcAxE1Oqp6XO4NAvlL6j1fRsNShraDotYhHO6WEygr8QOKFesEozG_8bFgM4-dYjSJnmmh2lj9OmzrsYTqIB-eaqP0izpXKNBCQqDfLJdikYt6Ue3g1j-DQDJmzrKQ5nJtEsnzXfszK2cH5nQLhTe57PbdNzb6QQTGUpAUiiNKJepnwDV0MHSBQQ23Uu4LnAgzX_SzWdVxY=	{}	rule_240672
6305231297	+923481452486	1BJWap1wBuy-B63XEmY85MGJQr_5SLQ-Bogs_kibYHVLHbylKQxzpu9TAJGoV8JZbPHqRVJOKG-Ev20o8ZBO7YrxeM7jR1uh0HU1PMBKD0Kxky5aFl88nqDQx3RIPQ7K8OpBw4nR8xVaP6yaFHvVCubL9BvWuIabssmUz7k3wRlk3qjV8cNQmfJy7NcK292MwRFBNHqsiRW7wGDSB4XncH-khBpEpIICnEkyNcuasZxl7ZseMv3z4rY0c7qATezU_nKqOtBpOVoeMc8CF6Ei_rHR4ai-K-euLYCN51CfpSi-1ZKy7aQexRlSoUD46xlQU9nAC1EU5rLSvi5aaclHW2hOQcATz0tc=	{}	rule_303725
7319777571	+919546197123	1BVtsOL8BuxZC61sCwjPEgbpFHIUm4hZW_2jbB_aFr3jeWF5Zv5uwXVrekQwwza067l_I5QaWcWdKZFLj7MnREtJlKBg3RGLr4VrGDYzDIW53yjY3yGga_Wv7VYpB8OzpeKxDZrbTmziWYkr02_MjOhHX0K_8lJzF5mk-2v7FwgaP_UMqu6-PfDxLahUpSq8LlCo6V0gEIynwa5HFfCl58l1sG4ipIsdD05w8p97aeqHU3J-e28YNOnIvr8tO1vGbt-DhYb1XQxdKiSbVbWy5QrNR9CYezPBvBJhuQtAMsHlT9WoopdRDmfMcd259tkAIEvpHQI1g7b47wsYbIgh4C5fBAlqbKM4=	{}	default
5663097688	+919585459672	1BVtsOLgBu7WHV4JN9KBkI58hvvjP7YKQZ9hcVqv61kt5VcnkvuNMudNZv2qV-7jQQ--8FCoGEwhFQKKyCPJAQk7Srk7D4KKZpR00UMQBTHxeq7y9AkdjZXRS6GSVavCecCI-N1odEEDW-Uy2jo4T9s0mi-BedJuGbFos5PStdFUGLq7v5OLS0VDceI58NAWr_CYpjsHxFJjHjKZa_OAp_sPbxGgPHrb7_wqi57WusbM0mr3KUgLfbRra14dK43oZdGkrmWOtG5N4G0zPcO9azTc0fan_3I3Rbz7z80tUQt4Uo3H_pSlBEWIauuif4ZNdCPhjHIYpsOs5laXbZbor3N5HQSNT2B4=	{}	rule_209096
6852552336	+880 1937823200	1BVtsOLoBu7hucup2QjYl54gfBoC5FJ0_H5zmbztxpjnE9ySfXuvXRuX0E9L3vlTg60xCSlVdV8Kub0Fd_DVNntke_RN6mQOqk6hl3ricClZAbuzjZX--u3vpouVDvJCVoVDr3zZR_-sBzSDXP6SVERAMS5pAduFBG5tvXqGcT2WSupKunJXHJunyHQ3ZmheSqHJzfBPqjI1wYFVxE-TTMQPrSZ2Fw_xeAnOXAEy6xAlA2r8YQf18NczCDDhBDxR4vcJcZ8f8ogQjGh5U_PbOnCLQvXJIVZ7FA-Q9lM58zQjfDKDDU2xDETQBWj9vFGqf4yT23lCOfVszZO7G-vrhmD9knS3QOZ0=	{}	rule_550358
6779399346	+880 1329346473	1BVtsOLoBu3J9krFqJ-opXHNV2WSZges-msRqd5kBvl0NlzKsqbUEqeehfPc7ym9InGtTQNV8u4eQDEb3e1MSE516vAlhxWRBLJ1Rw349e7RME7eDQePQAnIdlKnaXM0yuarsQ4pUAx7M4HEd1BeP4rdiKngECmllro8NdPoIJdBxI2j1Jb6EsXc9SZ5Oox26ZMVgRLL2JbaWQEqiD__RE6d26s9GFFaZssqWZL22tCIYSSeTeJHkWL3j7HDFpUgKA7uz3zkE5H2KyhKhujpncAysS9QfRZMVYr6J-zHC4JZsqRf0gF4w9H6f4fIg0j7WlXokaica2AubLQpU-YS9uwHN61wLcFw=	{}	rule_550914
6078490717	+972 53 391 3423	1BJWap1wBu3ZofyJHADXws1aHxzMXJ_w1BjcE7IqWm1BGbwSZWmDNmOupBkWzBBP-tMPN4t7sCy6Q76eWqnkbxN7cslOjcqS_QODpD_8z7Qu3ahg6O3mPslpNexyd22hNctlbesFOMsQ5UfW2W5AADdr9g36eavGAobJtamhLEpFjupaTI2sz2wM8muv1tWjwtqNLxAeNRzzSxQiW6ErVFb7R8d_ym6FHoWCGiMMxL9ThD3DRrJ2NLl8j9M9EHVed1Sodnye1wNlRcruFioRZm8xTYGRPXpxtaxKSU2GqvPoOY4hRf5B8VBz_BZrejdE1tuPR7c3ess6n4l3lzNsdlQ8r2PPu9Mw=	{}	rule_558274
1608543480	+880 1983907440	1BVtsOLoBu04mzKVdWGo30egCAcumhPLEHI2r8X85V7XREsTfSwHDMCsyk-0YJiEpbPCfcKSa1xojD9Spz-kWYDqRtJAXJkahpKNhghcuWjkjq2enm9oolPXLsIF4hwc-fmAl7r_4H7syTK5IqLPixZabwtwIKcgbE9SWeoN4XQ8KQDTiwi0EJlMRcoa_Aw656B2uR1IGYfAFwZifALuGWv-sATP8KaopeTLnBzeoz2HbPG26L-a3SOAUpPl4qJjjxsfzGQiAIMddLBYAaRFyYhxwyOAVWQUk95YdOTiDwdX5IOq7D61ww7DZ7bDw3Y6Rh6HMm-z3hUmMPMArZEbRHROUOs9Ahdk=	{}	rule_569251
649455144	+919570206252	1BVtsOLoBu0GpwbQbyK4MYoUi1005OyGwwn-O6Pr-v4Y4_U-e6VF0a87XI7reexNsGVKnacEHf83jm_ugNbvXR7TpBKlPspgHZpoQ3BuukoPhuCYy3Z4qdURPaNcVF272tL_yiAsyNVKGaQBRxM4zFPI8upEHhJx8oQQZLfFhnr2VBWve7IFu1Jrb8THsMN6KeV9ex3RBhYUnItdrhNEZqqeE3nqFCL93nNGi-ahFT_XxNDHBrgfCngzgHrJrSdqbofUJ6eth61gDzJhq-7d1KGRUMCtE76qP8g2BXB9d5jwT5cuJbQXMMbx5KW2QufTAECcOFyb2A-yS_jPB1bGvvykFnSR9V_s=	{}	default
7880089937	+639097522156	1BVtsOIcBuwmBeOOK2PidSpvhBqe4CLFtafcT-EXmTWt1CJ5xx9ia2PsNtnlNDta1MygXWw0xlrUcVfp3LiCuPpiDn2KPx06J-v-GDE6TV3Ak4rwBImYYZn-JW07xBsCbJsNqyJR0Ja_o_XeqFvC8HNk_zkgl5rTIwk61dLuBxYXaMDwtkTZoD6mPWy366cy2SAlJB96te0AzSNpRzQCWVyzklTgVRwaEJf3aPt6E-cBU22soHT2uVPpOf6swu85_sKXlzmtEdSzsqDmzX0Ivv8Jn4hLfPbnXFWA_FMvfvgS2qlUqprE99fSzWDekALxrPovSu5VxR7qoGeYPPpp7Zyysb847jhs=	{}	rule_690508
7430101095	+8801873199644	1BVtsOIcBuyoI0INToOhjEJGWDXjLV5N_-McKWI8EGHgCF9j7H2dR4LJgAR2_s1SVaeFzGORmF2ABvfJWYfS33TJXNjvUrb5tjCJNnYiHZvcN5lVRnSqO1i8TmkzD7QMywZjjOv7IUDoTmjuhyia9pGYiqmXHKuCjLwuhVxm3YnNU15RIWCWEokhO4MKTJGNhaYDUfyG_Ip1VUEySUaiHrNBhE7Ooc6dsZdIKM-ccp9kXgDq9GKINNr8q5puyW84LyHHQeHl7yzWxFwb8N9QaIUhPRY2nD6LLf8XlVjPxBI4q_t8DFrJvZovYayI1C7UGH-5Wtvp2dJHNYOtyAIercxLIECnZuwI=	{}	rule_672142
5964390462	+8801716125274	1BVtsOIcBuyohz0QsDlpB4LAaGN2QwrHa2hiBTxaS036TsVfX9X1R-0EilKXpW7boHvUKE1ma8nsn4V1zLKW8uJ_hdDL7-YDfwsRUnw3WdDWNisIGHIZet8FXNW7P105V2sKYrhPoESuOzskxM8Wkue3DyOEe1Rp72xtdAlc2w1B4O9o5r82m5hbTSd9n2V59jeszD3QuOiD8tfDaVPfkllLD8Du-kyKkBoTt2vIwrJjcybKA2P_xgIRZVOhwhGxYZzjDWiluzQsXHjjYQNEp575_z_yJAQYxT-4PVSfa6HmOtF39QI-6P0ZQMCB3IeGiGyx5qaQl-oS85_qZGkGsvYCrgYxLpgA=	{}	rule_706573
7752022043	+60177143686	1BVtsOIcBuycGJn-9pCwNgDZjbPmMYWaUKqSBiSToIfhpRcLHsHXBWm16UMe45njeHFfBG_Erj6mzFr6WIoU-lnLCO9N4eD7IaoSYEEnL38DmdCQTcCimXJmynB4SCWxpgYUxwwqVETOkY1I240HawGj8G3Zc1eWfKriz4Ev7M_CrsfFW6xF8IDV11w10z7Fkdgg7stXpxL7kDLx6I6CHs79d-WHvWEeFbnCp3otjDPfmS95a9v14hoqJoyjJrCiYN2FOs-01j8EAygWdp9bqoAUn2eonbFoknnpk1XWXwx2QvRdGAS_mTVpY8TJaSe2SJKU5_KEylb8hBFuJDzf2bpLxhre3gMc=	{}	rule_722960
6876778776	+37253618297	1BJWap1sBuwLY0rtrc1cXcE_-5z3ejFIh3m8bX2PBwgxI1ZgziTC6nfTdtGfCoaJoBVPpLI0GYJ9Ti9AQkPZRiq3FKYHAPsrJqpAIw5FEp0HjyWY0n_mk9jdEfww9K4JV9sK-omn0auf9XCGYK1JPml3k_wRbVUXusiSZ1uUPvHxI-5Yb4-uO0J-UuDnQN7HsPRxjj9N9YiFweDPBJOkj7lg6mQVrPZMNtYfag5uwq_tiFnOtgn9oIYln4bBtKoEnllJw1BtvnP3NWWQkxFfmMBzD-mAbWWAgVgY3D0gm721MeOmiezm6KzfefosegZ2mGHDRz8ImPW-3DEiVK4a28Np-OidgjI8=	{}	rule_761854
7811318319	+918373045680	1BVtsOMUBu7IJIDqsjQG2THfgOLmbohp6DpHJoyb0D7rrHm5jlJe8lOeUaQyA7aYzAN8SRFscyFudwIAELyz1MrR3BzExFDidbfER2HUxWyHM9QerJZGXltpGPKFlIJSvkNLi1NNLqXX1Bom9GSv0HQ_o0K5bLj56jaq1nUBOhlC-3Aa_pOiV_aG6rIVJG_0njVr5_37eoqpnE-yJxS1axTCCPktINcPUDAp8PybkiigiMSBBCCn26kqw5Ebj1Ml-2hMxtLtvFWbcu5hc1giEOxoNTS6MBBzGxxP6SDyupvI9_Kzh1fn1QlvNg0DbdS0vJw3cANgJMAVIOR736K-IrEQZvp8Ls08=	{}	rule_990550
5689065087	+917355768424	1BVtsOMgBuySIgVSI5Lnii6lqmkQ7lwoNxkKXVcot3Tce9S5Edlg-oWoQgxrQOVoe3R_i37eCejB1HyfNhC4zLs9zq8f1HVppxyeL8LuDOSH5ZteCQV-2CtjejkbZsjNZ-5CVBCJPCMcvaz_zsoIyIlXX5R6iCkDeprPrVYc0QgNVltmY3jET2uZVLfGFM3RvHs2JpbN_2wNxu0Eo2q1iN6-1_uSTs78HeYafgoW9GHcQq2y-n5gZjy4K5o23ozCpmtcr1-Jgt51-x6pQd32aEB9kPNEQ_k_7E1MOzQzV6iSmAvAbsveMdI6LqPayEmtmCAzZ8hxz0oePBPqSUvd1jBlEKet_YWA=	{}	rule_536552
6526942062	+918492813874	1BVtsOIcBu70j_MTZpDcE9TWLTJHirDjjqNJq-15jl0xkxi2uNhq-vJy4ITZcTRrwNPFPoFcMl40e9kwMbBCrw2zXVbZcjCfUUVCS525BNGlYRln_4wrLy-gJsT1jX5aYysnWBNtAvYoldGxqGGZ3njwkUOOiFQddpTaLX2mJXL_XowfMyfEAOqObA5CALfCXJ94D_mwiVeoXD5pEvl1ctBl8g46GCqiklV7RjDzhrflp2HjLAYAEivk1VALYPyZo2ksvTzn_SycTNU4LRhbSBpeB-IB1MEnswGZKH1a4n1sblBq2QwW_dD2aeExqsDORFsuHv1y3p2mS6aJsyT0pL50dmuO5TG8=	{}	rule_804606
8243850085	+6282342832877	1BVtsOMYBuxf3efYDpgRg3hcyo2EhzITtas0WXbDgMx07y8hwDNVGrGmojz0Y-3ffH1C8AtaFkB5B4Yi0GCJ7CfEGyBCdyy6folICQJo0fgQF4mFAXqU0NmjjN8dyezR2GO2_RCFxIdqkA9m37VMwQNkjD24hjY1tElxCHxljd55jnKuM6zLA_DZywLnZKXcZdSTeM2IJ5bUBejRjEsloFhKAHH5kcQnnPc2qWSoSh7gOYcIojYA-FUsiv9koVziL6Sdtblj5V5-btU9MBcZSEgVBtLTgsdGHVO_J4hluZ1haMZTU0UhA0EDExXD3SfoGCUOkAqmr61aqJeuF4vCkaZ2ysPmF-k8=	{}	rule_1314518
5803322217	+8801786584775	1BVtsOMYBu5I4jsNtOvOpi9ScfbZRNmxr2pB_2dmth3oSKBm5X_vYSByMyqL7QfSEh4t8zFvrE-5aZWbgT-5R8h9pl1GwpgJKNsBhj-X7Med0vKOOr-7TF2aQQAynDM66RysUxYax2cYcwYMIPOQq_035gDOnK5r27pG_eoddUHe7W0YkIxpKulgW_8FLbCJOeslnFBQGH9f1VEUDk3HaRydcHghfAIVVQmdTca2dJadXo4L4aCcUsvLAd0Qo0QgiGVp02XumRQgqtHSH3dmncSbhcR4QYqx3KAQQy4B7jRkHFcTCNXCutv3JaQ9XHC1AiPUJ7NUgvohqMC8x4LRdgrpK4Z7EzJQ=	{}	rule_526652
7224107415	+6283846783674	1BVtsOKsBuxdl2332OZnG_0f5hFVUZfsVAZgA5MpfDwXsSQOntqyMCBXOdH6QGXl6gIDWXNWtuFaBI3iJevtA0SGUHopZP42SV0zvenEGrmboPKWcl23Yqgew24SokmV8Gu4bnOnQcqxcO-_GlzrOc0qYnT2c2mhLMEFYKh5CUu4DwN0jKKntJt4O4If8aR4crdriTECQUtDXpZ6NCh8TeYuTb13-J9YK1ZEnxSYMzvAkeoru-5NO-4-P23zhTFs3KHEASrBIjTM6u6z0hGR6v1qAaGVWEQ3U6sO5gm7jIMzddd_vW9Pr-XdmvU57yqwdF_29A9IVAL3QfeeWW8s82atYl_C3cKA=	{}	rule_864307
6366929184	+91 85020 75166	1BVtsOMUBu0KxnkhGjBt8vPh_NpclWEwqnx7b0y8olCoE7BfFmSi5y08kLFvly0cfIGMJ-C_nopd4wY35Tv2HfzmhV4MNWnIAirvdOiP7eUR13t3CcSKC5Jtv7LVdkUXzZfbt71SsHh3H28R7ubpzlbwJjEffC3ESI7-EjDXP6r1rYvZKvAKyyy3Z5tQz5CY_OphKcXNNL6-il44GNndY41GBnv97U8CYvShkihA7-Ik5OBUdhwkDu2wvaKjFoQu_WXzzQ5FOYFMOLM5q9UlvvkP93vrC4bRIDM_ySuHipGSL8LUUW5VIXdGQOqPkm0E66p7wFQy-3W5t4_R0a9cUzryPhQLCNRM=	{}	rule_895029
8382351343	+8801879168323	1BVtsOMUBu0J2s9bPQRQpNBeZuq4vK_ZKdZUnISNeaOQ1F_vWSlaEdfx1fR0XY65jwoZnzZjnmWPPBt8xq3Bf5L3zvDby7TvyegSui80Yze-6qCjqZM753Rr8YNETZOWcdcdCu0JlLv5kOTrRb18jmEZleO_R8go2adLFpEw5vi4-AhNTssRuWpNxsMZMWNL8uIOt-pcy9WeewfXDFzVg5xAyie0tP95wgU8UFCRDzGD-7CsPAyOovQONh5sifpXcSw-6J06K7EkDehAYjGWIUHWG0A1_Ra7IbyF9_BvpvADoT0-RMVq6fA7q2E3tj7fqF-d9Fq94qJhYKGE5D2fbgFv7UhFEHZQ=	{}	rule_933468
8260737582	+917851862669	1BVtsOMUBu13fq2gP34dUxaGlaaw3QJv4yrMw_vlJnozL6EtlxbxSewfdczLPcQBYAsF479NQPsocPd0G24rrr73AQF_897tKEkHIZ38ZUQdN8hnz6_VefFqne4D4R7mYLExuyQw1fuzLLQk08niRJx2X4HbQCeeMpssnDET_8dKXoaWA2KzpQ6NKuSjk_Bhvj8y9t5bBwjeDOLJ2mP2jn508akuJcLt_OUVB-4ceTKAs0rVdnqa-8Rx8ZeLZ5l8i_H2x4ab_3IpBR1OlzLWEi5bqO0BPaS88lNVFbzWuHWHEwCkJycjuemFYfMjxuxIB6I3WkdQjVFuxB8TI_qgdLdh6L_iuuDM=	{}	rule_1068508
7803536162	+998996251949	1ApWapzMBuzknBUefIxl4VOLRvJLj_uJkWsjoZMpaDrazrmlSqR-V7bSeRaU2zAl8HRWP6_l_vmxwbUdQOpPueVmWe0aKVYnHoQfQAy2dzqmAiiu1BZpZLToL50ovuQcaFYxzeMm9LHCcLg1afnxMK9f90gd5ckoy4oSefM5MBV2duojG3G6btPYodcaqNugNLgEmbWrznPEHit_gtGSyjg4sY0vHDNBhlgUxT8qi7SnHjulYyUbxvKVXhOcgNc8sNG4evjxJKdzXMYeh8hvsNpzRW_8bblKLUgLjNtvRhaQX1OBgS7gCuCnM2hCYO6DTnT-rZb8e1gzBIWvfqa3wB13gRBv0pf0=	{}	default
6570157953	+998959679292	1ApWapzMBu0KMF-EJr9ar5udJRdKsBudgmNLWx7NR8iFoIJApWdBtWbl7ftbXDOP6nWFMoNRtJcwQNzGOBOXkvMmqyRtZKml6Y0dH_5wYIoA5hNNvf8xvP809i5DAXnPqeLwBGMMj5Q8L3YWcZ5nxSGK3-0QG92ORblkJnxBBwHasU7SSwhgxSvlbaYg5pVlCiaJp4a2p9s_1mWrNN72XF0tNQxrGneTwI0M9v72BxZi1DKuCi4S0ZzRJ2Z3UY-sFKROCnClFF0X_bHJ3c8F928DrpZA6ZtsbZQK2aNclgxR9CBmTlhOPDwr2ONhyJa9wqIL7yHHssBoUxSObXSzZfb5LvQSxySw=	{}	rule_1164447
5445031425	+8801636484525	1BVtsOMYBu29-q980fE60AKgMXs1zNrySfNpjqyaLH7bLewLS2B7G_b6Jfxad85YUmtaDHm1I4NRauDd6XbcYWvW-ecPP7R2E55m9R2rUqbWH_2s7kKiE28o7uxRA_x_R31UHzSdoVekKHwqbliXvl0IYkUDX0PjWL-czSWKUfzoLey16yuv-hYWC2Klv4j2wh4XnioHVj6Q90HsGbN0LPsI-5N9MTC0zmdAuAzTpjquTlNDkaFO_BiNPTuUhd1-TxoZ4coHSG1uKxio1r0anDZGrG3m-MqEpbO1U5sfTB90f4mbWNGdpEpiR4-WuVD5z28JWNFhsGLEUn8DQpqDFAT-JMKX49xI=	{}	rule_1334710
6551218990	+9779842105790	1BVtsOMUBuyOaghpAZJ5ylyArzBgMCHn_LRFnoW88kGZI6L6UtnVGXrUA-dJSiamCX42nhI253-wjzKL_THD-XDwsvIiAN393ufNugTT6-Thfx_SuaUnvTqyeo4UvpWrKTHazYajJF6ctj1uNhBuHNmhWeImebXpMOcEkpM398dzRmYsYZeCPR1TheCKU3QUf8eQTO9EqwQYLmWwwbIJXfOEbpBPfNqPgClDjBlwnYdpUd4Ii5gP0pP_AjQ1BljlIu-_TWRSXNca4W9rsPvIFIawdDztlbTXrgKGsEYJKFVTghNyMlzHcAi6c7PZG4gAlhZ0RUPS-E493vmBX5AQLVtvpdMbPVeM=	{}	rule_1235124
1444313827	+919014188862	1BVtsOHoBu5F796Mpxu4QavMi8WMs512_tBxHQ79eYPcfwGlNJ4BHEr6rBikauD4OXJ4Xs94NWIyj5gAd8rUwQa2bvVCI_hlW2DH8wLZ-2Q6Y00Pi55efIGElO_EsV6JsdTjrzQT9kV7kb9NnNX7EH5lHzANXF6_Y0e9JsB67KXYItSoU8WzLQyjkF2R9-sO8Z7NyT34553feGsAeiTfQu50CtZYSz9JIhE7Jt_10Lge7uAf5txgVCVuLuC-BSwr991CGegBSs0PBbA79gr9XIeikvs4XSpEldiZS0u4ANr0dzukycrEvwh6W11Z1Nb3eK3zbPQsGZ-khE8CyGuGDZiyey9KzYgE=	{}	rule_626518
7636116711	+917565006394	1BVtsOHoBu2e_V0gmaA3unoB8RVcqHVAPQYoOaf5F_UGRk51MIvxvxjoZvR4ppMTG1cjP1AHyfMYie1AJjy5AUBG1WqlkVRAGzqf_EEMbirRbM6PcdIiX3bk3gjJafE0UWs5WS2Ng3qHvCr3gt0p3s3pdmYw3tH5hsKHOyT5-j1rMgymn75WYGvJ-s4RF6Y-wtcAkud8hMbcGFJCvf99AZ70xP3L_v_1rW69AUzhO6F0qAOVY-cRIxHsX8sIY3HtEQF16hIuEjgxpzx-2d2gkdYIJKkEeNN6Q7J6XOJPbbi3hkL_SL0jWDAt7Wwrp5fZLr65MXLTyRpgI-NSiuR2VME6bT9bec_4=	{}	rule_1491584
6082027138	+919339812307	1BVtsOHoBuzvghuXBre5-wO6HpcXo8XrwPaUweV73G5Ks_OARf1M6wzAhm7IwRrwnYwwi1dYg4DxZXXB2LTGDzJ0N4pJBV3aJgAm6Yht1DzB6ia1cFEzhgQBtTy5TthEc8K6SzhgXKrv02xNG_vQuMvbA2PaW1oNPdIb6XmxbJltxul_dF5ef7x8RWdBOQ9zy34QxJnTw7ap3yhLAwTFdvxDs-vn5Eg0UhJjmGZQ8wL-r24uJAWyK5V7qBK4WtyrUNX8wJWVW8o41NnnYib8Y1SIWYlhwJUgD7A5TG7_321r24BdeqOlaJBthpdGDs97GsVlXc4J7ytCQfIOd-550eB0WhMMl7UI=	{}	rule_333452
8276262057	+989981899668	1BJWap1wBu7lV3sKVaXQrUHjfVEobea3b_uvtcz20o706LCd9UY-oWzETMUpe_EMOWiYBdOK3ZM6NAy_q9XEya-v1dnKtpcu-83ByZyxSQExbgbwiEXg7OMKXzb4XA1TbpZwLUNyjtyr5c_3eEHjhV2X8Nt2AdwDmB6pUCgmxXEj1B4wyml24G6FiqrDdeQP6g9YDmvjMvRf5ZfmT47ODGlNIp7dBPwp7NUQg143qJn1gAO1QqKVIGeHyTFfBegNiAzUF8GRWcvqU8qY-C78_B_XgHQ1pgRAAZg4pXZ18dSySepahM-VxSgNYRGTCzH1FLB3XJiBhpxO7j-pzjVV1BFA5hNsQiYU=	{}	rule_1682557
8281707866	+919662339651	1BVtsOHoBuwMwHKiLm1GTL54e2mOxwdNLiZeJwhV0nQEW0p8m6UXsiKm2DzuGEcSVivUO5wspISLq3idzSU1sVZkYtOi5sfMneyiiUa6gD-RY3n-tdG-Hjri2UR-4KPytzANVoitRkEuyXccQGR29Pls3OuFqHumPcML69gJOHhDl6gdjHrvVK_zaV_c8URRBDm9ZYf1QB4wdJ_SM92vO5wRSC-UV_uxN8z1WUBI0zZ2A3k9O87vEkRUPOOQ5eTFq7kdC_L6Gy0MlhzGtPWcaC6IsUvh_TNfpwuNAVloB_2TWO3MiFmb66K97vpTt6IFra2ZMULz0IgmEMoO6szj8WOCo9HLkuUA=	{}	rule_1557538
8106692932	+919067510682	1BVtsOLcBu48_0WZQgN4cmGPaaLLbtJm7arMmIvVxLHFhOESXQfdr3tXrGRkMbpN5z31bqT0FolihIH10lTPvveNRf2k-v6joYgmd5fXwI5z2MZykk0yv__5r08vE9S0YUCfrhBOZ6cDj0I4Ivl7kXkfvAD6Rel6LuIWT8_RQoCDIgUManPJy8V-lzOOys8WNYOFZqCaDdmNV-7pI_QBGI7oViQDmHfcAkx3w4C-W2Lz9w5k8KQnTCFZxOF8yTXHnQq7BWnxY0saW8gBEMSPVW_6K_cn4V69qvuu7JtvGqnQtkin1d91SvDLE0MEArtnyZDfi5fKSq4116jU5ldn4CXTUGG_cXSI=	{}	rule_1839524
7962843287	+919339377809	1BVtsOHoBu5qGuhNF6ugpt-CPHM_gDoc7S5I6VKI_7Qr-Rd9an-oIfMTfCM3SoCHe2c-qEqeUHru-UYlm-G7x216BXfpCFGpEmA5jFDRFTmtSMHyzhyohZ5MY8pKX568jLbZ9IC8uSS3IR_OVs71a2Gm9ZioEBV8KsaBKhVKO1xUdEq3Z-LoqJ80mCmhq2V-H95C3opJqWCoUVpHIZKRUxResOsR7W6N5iZqRDsfnDUg7x5QmgTuVgj-B2taqJrTrRR6-dF1A6CRfDtHXuLCKrIJw5zZTcSYs2KhswR8oGF4jpaqwznDEKKYGVv2idQZm6XGjribVB1d07JPbM-Otw_J3qkLgv9I=	{}	rule_358910
1414116736	+918839809726	1BVtsOMUBu4hvERqeDciB39rHSX5145mu3Zij7bIoQG_iAR95Mb_dE2uEGqiQ7VejfoOXobm71LOw3ugCgrZpbB3me_OBlx6noleMp_OudhClpHi-FGgareZMcb1WKwg7B_omhyPPEZmp5ZtyOP2LF-ge8nrUmZzl2tHv9OQeGllTnuA6Wrduiw_YeTzX9L66ZNMKWstxXC5MPgXmFCVC_5dkvqc2MsIfikF0DhVoVRqoHyWWNyExeyFBPzQEuBtyORnyl2vj0BnBtaY5KWUx-lh_qfN2-OzW1KRu1a9kv4DzZTshCo4R8ISoyOdBzZCk1HhJDo9BbF5MzphRs9WeowZAaokZDB0=	{}	rule_351459
7238808048	+918447772170	1BVtsOLcBu6TPTFv9RoxTww3VhaW0RSzwFWhsXvnHwxSrM96ruEkaS-Nw6MnOSFQdlno4wIeQdQSBbPA_Dw6msFZZg74Xa_IY1BSCTCpqsY2NWs2Y-6rgQquLwsmtKqVTimwVSKLYa8fh9rXr1Bu-6VfNav97noV9M4ZtRs5rWD-JPY2ePnRQfdyeWEFVQ8ktULrhcNMxSoBIFzZiq2kuVtGPVjfUTkveRL6SKDxvfZdCZftnrVzEigINgtklpNx7XI49SE4foZQGLO5ZIIRB2dWPilQNbOuBQnFwP2ey9UYwDBURbGo5VITUjWpzjFBOBEJE_Z_BbSu1Vk5JzmBLGn0ZD4OHUEE=	{}	rule_847866
8562904531	+5562994504217	1AZWarzYBu2sK6m6cSWsk1VsWMblk5GCDs7R6G7J8NuPu0DcPLGoB-_FCsLroHVXLhoJy8tn4H123lOl9O0K_YYp49hRuXMa1UhA-jgtE7zfANaYw3_8_tv7jB97YzBmZpCE1MWTxCFaF4Py1HsjRQbAQ_7R0cPJLRVJJOMoqDFVIT-8i7mdmO6RSjjhettErPA59A_o0NiORodPHo1JGTn2aJzF9LUs2nfa7O3alLLqHnKK2ac7h0jhEqoSlmbDt9uima7CgqrHTV9-Otgptoh01CNt6OL-Szo8GGdhRUUqDSELO6NBJhRLj-GQB5M6XsSkA7eLxUETB725oyOqMJoqDtIyfpX8=	{}	rule_1336
7866745942	+917856811862	1BVtsOLcBu5rHZfLJa29LUP1QkVEPkKLmeEMUIwfjIUzrd0v7JbnBssGs1OgiR6SacHMtqEFi-9iMu8LXX9N--xevF7eQ83XOr0a-CQOTNIY4Y-j_JYYLzJ_OIiaboNQKZsbblhCtdjWLvmws1e_aRM7gsFOfYN-cyFXDNkC9FjZ2LcJlDX5UhQVnGqLeuwAYve9m2lPQ3DHcW8uVXJkOgT3r4ozeFBh6GcNE4iITLahs9okrTqfG7BHB2hFvjGFJs0xBzSRwtRKHMjtKWiKtglhKGvHliZ0_Qpl3uq7iwHEH_-jc-n0mbxAgPL66ECji2W1A31hsQvymEV-84KjyCqMZ8PCbA7s=	{}	rule_1813541
6271999767	+18768342391	1AZWarzMBu7EoSopFBmLT5t_si0lZ-w2dfUGKsQCTYIAGtlQF_v1XyLkHOScwqQzkS85XA1Emq6uhTrmoH_2fDLitmhbyKagOhqT2LDuS_batZQZ7Z-RYNPVsMkr51rBY5J7QQX29m41s5RBym5mgjq6RhW5albGjaq1RMvZTvvs58M1JZZeK4xdEQWmyIhdCWnTPqLFUSGkt7gzMPlXbrTadfxGeXkvb5_mEF-Iy0TjWAt8_XnlvvArsVQMFVsJBTUqyaKy72nozNhJBycWbxy2-Z40oCo6ibLU7t8YNptmGWnZmk94IFHk1qnTtD2-TXajjLSPWeSfKzZguSa68hTtoadkSpXo=	{}	rule_1891516
8431307336	+923257694839	1BJWap1sBuwHE52TYU5yX99yADbq9PWS9uWzXpXPe9MLvurlAFIoyBaGhO8nm0W-32xXkLLatt0I4t9hD_XEQ0zlH4ZWN0MSjDodKiP11sU02YJ9RDvpx_bCk_Uas2GLvuZvz9cWFmhAxkeaEMKYYUTDcg602tn5bDnUbsRp6y5EKemxzPwTPV8TPsANquICfD3vYON1Yo763dqVT6OON6vfiYLZdzEa0Q9rZ9ApTrv8rfBKADXYmbt0erSEoE5ZtK9jtjQyE5GZEnEPrIdMuaXgiv8ZN6QZ_vLz8wOGYQt92zG1mstp8qEX-l6BzFN03Td2G4SjYwUvZuHN5JNY2A_jrTvcOqLM=	{}	rule_230046
6514739688	+49 176 25598048	1ApWapzMBu1fAJmQhgVwGl9D7V7inbefzkgI3O6D9lETPrVsMvxs-2Ihbuhq8WazgLiPkRmjufYx5uYHW053nfU3ZTUO3aTSnaz-M9i3b0aLYIbW-ztkvQYPgcLRR5xLHxGDBORf2YAhb-LFp30VAi2EJF9lf8K9RZlfPjo2qMRJCYbm6YcNpXj7IPlI2IbihFy95R45C5ZTbkkUCEmVYEBPxyT9yhrwEA2mLnIOxeRo76WPSl2_yuE1RZ9Oa7MGBTcjPEC6QYu9Vo0Xs0hdChIT4xdojMQ69miha4H_MDulHDBb8t7LbI4n7UiNM0X1AkajwRqJcnpYt9M-BCnNCSW73HYAzXMk=	{}	rule_119597
7301764474	+918876414998	1BVtsOMUBu2-ZFs6CDSGnByD-YHoMKSR8dUwfHk6_ZpIPQ9VG6R0C3hgzBfMzrybuIfJkmxYcwjHuz8HTmdNXUlw-8pbvTLyrlZN7YsxbePMaRnnxdWKTlhiKnqEAEs-WcABsFKc2jI7FZQlzeMU2SmDomxzaT5m7XYwD-v0ydOYzP_gw6KViqq0YlHTXYhEBcPfIxCt8aoHFofKx0cZvcg6PE05vL-4BddZKeRNvYYLJ2jppqDhlQRkuleoSKd8V-qQmVimaD5yeq3N8VTmRv390s_ZfaRic1N2lAx8EgrvXgaVetUQ_I_B_r9mQZltDdn06sLuOaSs8Wss0ct5veQHXNz7TC3k=	{}	rule_330535
8040370079	+8801977230344	1BVtsOMUBu5d7AY1hL4R-2ovtW2U8DB5zHTjVM2VLYA2SSjJHrsh_5qhlDFbEWZDU03Qm3mZ-TUriLGH_0A8i3NSwD0eOs1aMiXCl1_FkFIO65uMg6-ZgBIktzQ8l3tjKDGSDxVab7iZ7sEwySR814OgKCE9Rz83oXt43PAm9TYIB0vsEWooKPNWOGd6SY2bklrBsBXvqpQ-498bUDSSUZK8JifGw4kWRjyTFbekgTJgwZnVfc5EaI5TM5EWg-P6V7NlW84la-hlLV-C6fTJQxunEpqUmUZ6uIdZ7e5w14yzqIjnh5Jtste_-qChVh5Gx-gSZdkqej0--yeZGDtl8HIgzWDm3r7k=	{}	rule_424689
6818938551	+8801833857407	1BVtsOMUBu3OUl8HabNPOUn0-D1v78bQiH2yxF0SToA5HikUAcwOAq0VnLleo_9jJOrWHpQMwX8d4Ez3eutKjnA1LLY9wwYB6r2lO9k4wbs1IsyfoFRiaSPixFgq3wRFC-Wb2-JFaLC-ySvvq37wifC84y2wrqk_qzf4tjvxfNP50rnR0NEwm3e-DVQjGQJWl3NjQRvH7p1dMrhMSTFyTdLLu6TLC3xZtqKxvoLw4SOPNSsxLjI6WZxwTMQ2oF9C-jmS6EufqYnmnkSMZC7rhEH2UFy5VwI5D54ir4y0NhqlP0uq0xyIDbCPmugafBCnQwS7ewKn0QNFilpzpKN7Z6Hsw_5XFqAk=	{}	rule_425990
7246249229	+9779807615850	1BVtsOMUBuw3OzF7FiAvkDxXgE--_8F3ZkZCXTsLPQZP6Bhm4CJMTMJHfvjQO1fkKZ7ds1DsFmI0XAun8mdZkMUPQBftem-SFBTO4DWFhcw08uZWQf7r6DPjXY-87n74I_xofs7w13RnT_r_y0YKvA3gA2mF7vqm_IGbEmidTe9NSvydEBjD5Y65ii-n2-Lvz4AN1OlMvpHFo60Hn9tZA57CPo5Ns9BOb7ELLVvGQF6MTp1huhVdAuHpgQoIGKFRICalJPxrD9NwXMex5GMVSkbB2FH15I7iUI6z_VPa7FQ_imwODdx7K03e-asoPGuC4NpirG5mzWvCDnnjtPtcZHsRMgp6jIGw=	{}	rule_426101
6306052652	+918918352118	1BVtsOMUBu0nU4mlz31nZDmYNiwPsJ63e9-Z9NfHjG2uh69Xj9Tt3oRX1NQ_K8kAx0b4LmG9h-88oFUfRM-3xB5seBF4YsvYJxYB1N8ZxQcM-pyJOYsxApvJF8GmxXVcy3VGB4gK2EHfQD2oyBOnVuWLIYaGSjMGbiRZm1fFNhsuBNhRuBjM-p5Ue5L2JazMB7kB1rnXvfK6qag7OrHIfj3uXS1YiFUVihhbvWmomvlKRUnlLTKBWCE5MmHiIVEIJS-wA4HuGP8USt2hqcnl02kex_Ioo7dc--gDDkI5S7mCXhOgQ1PjHn7j3YdU_ukNdOsN4Wp6wMMfhqdNgUhJpMT1QF0yUI7o=	{}	rule_467191
6013957379	+31684162511	1BJWap1sBuz-zCnksL9-iJ0KNM1TfxluY5yLX_MvJfqZKTRxDftfd4L5vs8b1f0HFrffOmarPn_nxLA1WPtDvrY2C-T82zuwJmrzh5kLe_Ufk2YZ0-NymRmXKsz9DEotrWU8gXIgNFLV74BdyiXhRVAbKme8bwTPgX-ueBmCKYylJYAvah4xMbc12aATRbaJiGz9F-piJTnVHFHCjv46Egj43E1kV8xZkP0aSmyVxbnT_B_AdqgP3FbjilSETsOaEVKap8EhpHp-avUso3YbSfWSTomUvzt6KiTADldU1JIA5zphpBsf1b4IdsEzrYOijVexMUfoowchQ0kvsvYbefPWZuNWhPsg=	{}	rule_500083
530131604	+393394478422	1BJWap1sBu2_oq-VNcGh59kiqypWeOx4_w1_4T1S_u0O7nq9vPab-w5UuffrPGUV5yOYePU8zvtxFXFhkJcbv9xn_W0AfUTWWHFYJfKASv7GU0j_WKfxCJzrSLLtlBvIru_KdMiuermU5W3U8gb0diQfcvA4uFnRn3MgaGBKEtpkMihp8MP6kd7t0AsMPWYesxsaWylM225FgFDmGqqUMXik1QF1hkYtMR89kly2p1YinGpUAi4fHzG6UYRzm1uoEa0jRYuKgkQnX2nan_KWWbvKo1SLE6I0zi2aMP20tpMq_DQZaNwS_YCwi2kXfW2UwASJuMNE4AJMh1yHSiOjxSmAqO3iC2u4=	{}	default
636735577	+918295330303	1BVtsOLgBuwGq32tBw--VcleXgWZ5r25YYkUVjSrDLjtQu8oM6ww8IZ-LQdJEnT8UP5MRftThdoSCKXJQ4oh4ePeCoBcR_OaN9xk4ZPRUVRtOG8K1PZmHy5d4KIs27kkq9TQsgXCGpBcVlLTWKYsjAk6MGBgh_KdfxenwhIrJNrUR3EvpJ-c4IfSeUaCVnDYmSekomQ2OjzCdBQJK4cMRMdDSPyfs8YKh_J4_dQ0KH8y47TbcdzJffRhg4QaaomLmZuLrAwwsfzQ-6CGRiR8ErBypNSK6_HKFput2NcuZxWG7k0sXtC85y_2wfUm64MAcW4MbGLPSeZ8lmjTgkpwSSLifk7X5tBI=	{}	rule_629274
6889190828	+64211346665	1AZWarzkBuylmNCBjxrPwj4RRlWk92BPip1xgg3XGK-9Axa_Tp26Ly23GOh8vrQJBXSqY1hZzsK9z2NAJOQcTHf9_oE1QUdlkLPsuX5cTqrb7p4iD2-v5R8oVjsS91fu5gylwwTFaee1CBYyDlJXjMYdq_Dd0ql3Av_VYj9a3C-2xTN6iaL8kg7gmvyTl3AcLstOOuS84K3c-txqSq0RcnF1Crk0RPixA2TAaV-SVOXJNao0ITG451rbV-NqNEcdclf4agDfl31lWVQqIuqVyhiefRmNMcFS5PGFx3AF3sBXJ_Z4rSqqRWO6m-gE490QPgZq1riOht2KjDv6x651iiqNmgqSP63M=	{}	rule_652920
6806206534	+8801755495745	1BVtsOLgBuzJWJaIr8Pd3F2i1aTgnffajvZ_9OOh-jDkz1aTWf1stZizLrHwjwMM0HvSIz7l088HIaJad9-drsRR-cUsNaSYFa_2wfIip0c_squdnAHDRs-8YZ8lwWjeeClpP_L4BRvLjTsNG1aWGQG3I763er6hz4JqqukPhQ652Gc-CrKbRJZC5yCimxOi6yJd4-WVyL3j_bMOWaiYcwo6TAoCOEjSPXZ9fmpx9JPWs0E4WHE8PoUq3u9VzaPEqgnw7CKhmkfrW0zZsnqTE8Tcwbhe0rqPsXOChCTWsLzC1q70AXq0e-GPTrvsHtDIFjTXfIWhb3MxKWFr70b-K7Oqw1xlHAxA=	{}	rule_688987
1992060940	+919347454474	1BVtsOHcBu17TlnIMzUDGsz83JelWSiNz0zpTTG2Z-Qofv2cqM1c-LItmlTiQXddUuMhPYxPtc_jwX_MBh5VOdqCH8IFKT1zvkf1fqtBosBBfYNqrX29-hLhdAvqr2zz8_zz5_fyj57hVTw7pVWqogSV6NyEwDEwI5Yy-35TVquTR4gb84UBmwFTZVMHj81WqDR3Hui_vV1A-sju5i1WIcd1e5bwmsMMiJhlXmi0IWGGEjpwy-xdqd710dGbKayYvPaASGy47EbFRLJ75dB9urwXfuhnrlxk_H6Dkh8B2X4B0i5Wq7eGUpROUFw05KhZMnvQgB0Mhee2iRuQLM6hrQwBcqq0_R8Q=	{}	rule_1677556
7635975214	+918890360493	1BVtsOLgBu2nMO0XAAMVAOTq7zG9fTYXdxBfuQaJ7hTD3rz_IkaT_nrnfx4OrFsjChsPWdfR1VmNgVR-R-Jk20v-tGRUSfuTT4kOirXsFp8nEGmStVNY0sijVNS5tXAJZXDR2XJ1A6dJU2ib-jVMPpQJh3ce8gXDKGP1vYY5SYKWFV-O7hSUdtl7R62W9veoEggci0TOvFeQyx9OipFnjjRbQKmRZlCL64Az9KvQOGpiy07n0WoCvobaAswcipL1wSAJXokvRcszUw-byCegopMNiMk_nTvB57DKLk895UA5oBu7ac4MnqQaGbqDz3_2G_bHn6_X9G7__ABfeVHlpIa3PGcMgh_Q=	{}	rule_821313
8494703426	+918076625207	1BVtsOLgBu4Qk2ZCfMMBNf_CZ2mkAU1ATDDqu9gkGKziTA2hcQCGoMt0SjB-9-_81fY5sove7dk7YIlvGj7DPKkuz1N28XoGRK-ZYKy2SUsNtNLfN0F6nhSNC64VFUufgv_W53DctEkFjRNtAaQcspCUaudLQ1kzjz9z8_nxa70e_buk4Sew006POiK5_UG-lMkHsrrTsGgE-4r1KruDJMJjLeGZqXMvUzkVhJWtFVTylPzJAx5xU0-Bs15PqndkFHl9jbNSDBCWPhhVeu3aJZ5Xq17uA0AIUWI0RDwPg7LOHKmonOQl1hW3_8lDJGnaVWjfZoarkrgjYCXftNb5OwTSz8jcSElM=	{}	rule_831899
7353874683	+919001279425	1BVtsOLgBu7XvpZM0BH_qs0xvnvXC8n-YuW9oB12GrwQjlr-146Psx87N7DmCZSM0_5QoKMIX46s0lCk-aDPNxaIWACNUYPRfoQJPYcBo5XiYjB59piHJW6wdsphbq1_uVQe_rLGEi-CTpGnSznj_mKeVtMEC6NGo6NlQYyopNL8WWwIguLs03dGDtVJnKGgDrfwZtVwZkiqV37bv-2FS3zjXaWpmbftXTJWj7iBUfWe2Z2rLBOm1rKOuanPH8K7qYLiWcNwPYd7y9-wLYwQDOyjYjn4HFi1kGMPLofPkHq2ZFTLOj9bVti79rVSXeixgU_ovJK8X6w92voUVQgEG47rLVIn7WGE=	{}	rule_842862
6112363781	+919836645346	1BVtsOKgBu8XxWdpp_udeyOX1S1Xht74gOt-St9J3X9HekVpbLgze5DCUXJ9oFvRg4h-N1EORnHbVT9-cD01XMsOcFFecrqkzzxvYmDU-ynKX2_vFPPvRuCozcqhawtcs_3gM_RqIBKH0bZR440rJgBtxCSUKqgqbp6A2EuN3km3-i773nsxJTL2eOYaIvpBxj0c7w9TBOp90TE6uDl-koQ1dKp8ZbNqvjy_XfQLNJxqrt8UL484y2b9KjgEodNv4UJJgzN1EVYkCvRPj8-W9dmm4kfF2mnYsC6Qx0vBfR16MXmK6VxTGhFPF9zkVQcV4oUjfGSnJHEc9ODm90t5FanvjR07b6_g=	{}	rule_137204
7844185193	+8801626962885	1BVtsOKgBu6XMxjQCYNiUupcV36GCq9bhMsG_Q4DE-Von-0bLYaNsV42Wk6bk_ZSkHzvRuE5zyt__Jz-D7bMWidpEAjI5G-tzv_FVqiIRuWJRjR7oHPUdz4LjB0sBlvCwGISiJsiemxlXtM2Rop6IMIPWLzzEmzYCVdKtovn2LJJ6hbXVv98l5UGA9AWihFqzWCH3uWlg8Fg4NC9f-xRBigbVsDjk_qRQ_6i96Gj6exeN1PrNSgBZhkmqcbRCz65zgIzWzL1gHB8AmZuaPlgR7Z_bGbGXr05y_6cwsrwg8X5hTY-QoE71frJa16R3ltKANREVaf7Fw0zhL6zROeUGnCsOl8EaVMI=	{}	rule_120843
8566633996	+917044657254	1BVtsOHoBu3QYrIsj1vVXO2Afwu-F_ThVaurWrhnL1On-BNHdqfH1ooxTrSYMCnQv104foyQxPbtLY5IVDrmT_AQ_HcfNQYTsIUP7xz2bnA69mwg7QDnFF6lPic6-akk7UY3ReneVXXfENfoybFSPZFwz2ZslIbSeBbgsV2p59AJc8MuBr4I1oVitUGQJHoQ3JV-NMQek0ZYP2eWgvwxtPf10_FwTd3cTg_JNSABIWc_FbJkTYo5jg6SEXI4R815qXSethCzR6Rvk3WR2p_DA0pKjfIGa4Y7A6NdPIRopCBe9wrkm1G4gqJclt9phRcZ5EBepclqvEzco5ncyCjLvZpGnwaoojR4=	{}	rule_59028
8594095910	+972559299081	1BJWap1wBu0g7P5ZpwflYd8zPBDhW5kylB6jV9Yx829IZHFOmgp7ZrjQkjj4DXwrNKFkaWxbQyPhyCE8uQS5YGe3DqWLAfyf6DPOmsknLBV-L3IlBATUfoiORp0pCvq5_mrZFsifvSKQMYJEGK9_fQkVphsmk5OOVocxmO3Q82eWZ8-y5xpmSdCVF5OCiByjlTy1p7oe0njMYs63PBIQr3rCfLQi2Ky2zVq_fU7hUy7kMGfjw_JDrHPyZoZ9clMoGHCnS8lC3uLnXAUyGdqTdaIwLdQewcdbE6Fj_VmJUUQx9wq4QeO5F3YGak5q-ivsuNtDcjfXO_Afo3X5aCoxWphTrMl2Usfs=	{}	rule_36683
1738839153	+38651629120	1BJWap1wBuw3Q69nbPnoHVyGukRKceywbejJ44xOUTQ4gq4ePuYmNFDFymSkT1LuWX1DV6KZRMtBxVu5o1sYfua5NgkxH9LPBh-nmfS_DtpkwjQDmaawlGevcz6Dg-r6-CxjCylTHk2x4bbk7PEAXpPBrQ2IUf6b3pr2g-DArgCS3Ql-3LhSQJF_I83zzdZY8hGlbHqLnsG9VcDDkXLIUrU41vVonDprFZwN7UipmyXI-55k_GAhVfsMZLNzBP6ojwUovFDLNmdSVEehvzbo71Rg8esYJD0tFOIU2bjVLMeeDCWJxexgoTOyWpz8EqIZXGP5IGOPjpwXYLrM3XW50VvLH6LnoPV0=	{}	rule_307630
6901754242	+18292930932	1AZWarzgBuzzGGPHMiSvZ5cu1CHNovO2uAhxK4gtk7l_1F9OpNvyJPdBD4NgkOWaAXIRM0p5lCyZylf263Z-_gmKjvjDYidJ6M60MzQpS-SuRv-wjT02QOm5Dr82HKTyWT8DfgdTfWKv5CAXUMNXyHXx915VVWnh2SWriXRjS6pJ-XUqpfcSE5QSVIeSznPCy6UNirJNIMQ67AZIHI7B4rSq3Pi4d7uB-BPH8lrlyWqVFp_UVeP_yjYhBprrj4CE0nvGw_dteZA8mce-_aV0pMQ1vrK5XT1bRCKXGx9-2Wwuo0xZNHkU0oaphZmXzgdBwB3ATUGCp7kOYTyWyk6lv1g7SRq8ZLV4=	{}	default
7560420076	+94787569320	1BVtsOHoBu2gXOi94PgxNK_VmTR0D8yw-yTFFIsdc6IhlEEoJRAgHEvP_SGUqDJgO_uXDkMs0LKWbTPM2hmTQOPYvMfTjB3iaoxynj0O7SrhtGno0w6XfA1ynVHCqkO1Zvr42SGimeRpvXfDY2-VQB6yVYk28Wymw98H3ssphIbLEuGLpMATNUDR_mN0-QbTVeh_JtuacKLgKyMRJITUQbr5-2F9bSIGtZRFz0rIYZ3fH6C2aD2c7DaRkVHw4g1RB-NtzdgGrlnL18Fu1lQmLEbXovLEPCReE7BTlSjGfxItKR8FDQ7RcPtgWxtHeQxHTO6K6BjO5GkErRUnNf4rNWh4SpP9OawY=	{}	rule_108595
7841164931	+919128965618	1BVtsOHMBuzusW3vDJgsiewo6XLAy56s39gPsyYCJV9lBLKWu-qchCI-5a1ZJufnk1BdYIVaEONgcRK6Htg8cAyRj7zjO_sGUcfse2KBQEM23lFfnfsCXsluPgQ2lT_vdPfJaHK8iGUiVLQtOE-nbD7VVWhWEI7AIddGODWib0zZSFMDdRBBxX4twbs1tzi1sQ0vK8bkyMrSc-JVrgqVDdtXoyEVBxP1Fcb3_GP_50Yy2RIyO2Q5AsPHTJ_zryMlyuFplpSZnAcJ54SqLXsqW6rtwsV4komU9XQ7TRhAx_fCsbDvJbOWFW1Obqja4FylPFw9Ow2ppMrLqon6s44rMZaFPixzuw10=	{}	rule_354659
7047677983	+919229756146	1BVtsOHoBu6z7dmbo6pkXldN1K6_MwhBnfUu4mK8G7JuqJGHMAUL8t1gLL7TFEkPrQh0dU3hSKG8sXew1Ph9np2feAN5247VJfjzKbZ9ydMca7CD1egoB9YNZovWDLT-f5kcHLQW6r54oF9SOmEx7IoIOh0HLiupa1r1QSH3zASGaS2SA9zDn0RgombjMmB5xGmp2E66XmmfXyi73H6axN9wi2ptM2_kRiPMjUyBxN2N6ltulu9c48NRbrwGKAuM-OXP_uWjm8uY7uCeNARWADdTE9w2LzgXGj8XL1HEPYEjpEOgTWj9BIzK-8_bFFWdGRgwcRt7Vn-XiwYlxiBgtM8sdYfSB2Kk=	{}	rule_5484
8357312111	+917050435938	1BVtsOHoBu62Rse5mVxOeQqYayxxgHCUlSvDTmx5oZ6BSEz9jhzLFvgF1bjtVIt9JrynwgAcI81qzDjOzZ5KMe0UNeAxbjnrA0smjSxsrN1SAaqRznneEzHHIGqIKtbVy7es_UdVxaiP36fLKbkzCHsmI-bM-ZnSx88RWDCbY55kVKp7_Nr9Tbo0KTm2sVTgaSAryl_wkhgrf4K9QqavSj5TldPO6OtbqD_YbxKjdHQM_RpBTZRNVUGmt_W3fesk80r7tSY18DEX3FwuxzpywJ8sVumzjq4D8nlO6uBbTz4dCu9Gl-oWuAtb4SroXlzdnd6WDo9kqLA1iaLRo1_Afj6UlFLssQ2E=	{}	rule_6238
8358336845	+919717271033	1BVtsOHoBu4meCfMplTZDTQHPH5S8cPjXCGPs1YveyK5AvAGh1jAl5v4MoDEalMEf8zlinr1rHLdn8K3JHH3Jf1m03DhMfCtDVSoHgaJfJ6U-ManOLRS1sN9J4hcd_SVsEBXKAyobf-vW_O1nKu79CspPcAZchs2RSkiIKgUQsmiGrvnzz56mbQDFSUJJfNSXsOnK0DNd28VtoUUltBBrvGD5TDWWFl6XR20XrnnROot3Ibe66dzQZh68Z_pQi1jrlivkCRrkdw4l4GGt9gls5gFNEd3zAwH3wwxSAu9Ldm1Rb82AMjpcWFMZl9hYpU2KQrAdBE8CkqlgnSsIwN6q4ZJX1iCTTxY=	{}	rule_80397
6942557751	+919093334367	1BVtsOMgBuxrO-AeuLUgH_asyJkOGPoKFtGxLxtyr-B1bnUcBOTLifO1l6CbXN8zSfRSUgxpFrGzv8qdULa9Jd8ElASqi83gOa8QfhDdtVRHBS4JJNPq4-VXEqAtUSOXT_9Q9izMPhhYswMbZPVFJpq5mdoHRBt4tDWv8cUe8DvSMkXFrydaqN4xFHWoaHdgqmjXviVz3kHdrJyM6UHtl-opMtbXXyNF8B5C2N0BhLD1wTe0tAo3jgH5j9g7dLN63UAaps7WM6adouDR1AeN0ECZ2ioAC8GJVpriQFwfkZ2R2WaLMeky0qa70YjI6SDUili9INrAbb1s43lKfupyL3AOxx9Y3tGA=	{}	rule_128212
535085855	+917006091132	1BVtsOMgBuyr11pA5lLWezdxlpTHMLi6gEU1eZNLtmWW_jbXwq8OoGyfyNJ3mtFcwDsfd4W8n57KA5lQuP6roh12D-DGy8-IzfLs2rPIaexuKPQ51lI4jcYDCasONrkxcxeO9VxQ9KgPudAYHFjzKz74qjkaO-MtY3s8hIboFLAbFYqIrjhqxuAwnxeQOo2Kw-XJraFJLwewnyUkfbLT4wNk3B4Wk3irVAIvrXj87EBblppBu7Qx5hVzjESwBZIBE0X-VgTCn8P5zjp9b-I5vXVnFw8NkoyNGbCR5Hq7t1xBxmAV7IhRzw0dDXCnpjfO3HPYP3nbt4COZgaEUXLDDlgP59Oa6FUs=	{}	rule_332600
8288097205	+918371054739	1BVtsOHUBu34crPJSwQVyG-q_zST2hoSpscYknURhHcYXeU0Fb6JEUSvBFygWJsG9Q-r-J9EdR09XduUpdrxKJCdr3nkXg32fJLY3-CUUZpacIMtSvHky03hszFbRrmA4VyszCWW78dRWqo0bsOSTFtfDm8PiyumEmclRxVWz6OzbIWEQugoATWVmCkwSYQvVBtYhxqfgvX0OYAFwO72rmhtdz_JN0fYtAKz7bjsAIPT3EJeZgmc9aBnL5R2pelCxZl9XVYTEPJhWGQCBUUIP7qV8-YtHXWe1XmfZk1P5qNYM8iLhYsQ5yKEKZ2kwIctd9JY8vOo1c0vlX7OzjiyJDOt9g7KIuNE=	{}	rule_42011
8291148450	+19862570592	1AZWarzcBu62sKCQrQUxWNmdFmyeE82snd5X_F9wy15AeAtfEoAp68ZUCIq3INPvnaONCSqz9YhVeZD7u8S6g2JIZGC94IemiSZkz_IxevD4r20-nyyCmpTJrnL4zKVOSJlFwh0GWwArglfJ81JnOVxAhrYlMV3fcXxAf5jePgIdRTvOKsHnP7mN5TUCAe0YJc5lCM3ezPHsLiXkbbNbIlctHyVibkTopWyLVF9ECvcWCxF1al9qtuJmGKZou7SvCVW0qe07T0mWvmeTEdvxCpuTEdOzQTE9Z-Bdw968x-bWS79pko8GUOhuliT2zBKizUpQguDboHNBefaqeLdnV5lzRjtX-tDY=	{}	default
8189961029	+959792709925	1BVtsOHoBuz1DPXToUwGH1hdSJQ-3VA3r7Au45fZiSi5xFQvax80lXAwtHmfkVCblLnihF_bx0Lgbd9iZmM9QLl2t7b3NtRNQJ4GszzkQEXI3mCY6E1nrcLuUK-AaDv5TeT-nT6lqmNA63aSrtfl-xS2xr93-4sN051r-bl5JJ9zWpkTVIV5S5n8meqq5nA2lczo5wa__0TcD6DYRQb4s7Y3OxQzGiGWlmfptlSDSj8zRwbtafscjQkrgwkq3Zt-9r-0QjbUwgyjr4e7o1UQt94HFCUa-wLyGHkFyfCJOKjVnvwYm6cLHJmoPhiaq26yHLwtdozH0Hsr2uLSnLuW1J97N8u6s5GM=	{}	rule_208072
7835273890	+917027366358	1BVtsOHoBux9E-yipIKnLdSd9fZ4IEgztacWpAmN7a-mf1JsoVL_NkwN58ps1Jn_17j2dkS8kslxlzYJmIaTvBRZn4zmLWhNyinYyF3FQEXCS4zowbtk8wyRFCUnbJA8bNKTKZDmcTB6Pk6UEDib6PlUsMg3HSc7a65CdpU17KwzRCVKPy3_VyN5cX-v86puCNxzioFvEVVisk9MBkifKSdIqykkjuBhmJhRi68CmgmXNVnCpLBYjLHp1KCiUbUanJk-xFmJjtpcUIC5d6pZbHDen48UJRT-ySaPVM8eSbkD4g1bjfJ0VNNtCeX0aTHiTSbeFx6JEtaOy0rcrh0auMbJLy64AmT8=	{}	rule_214257
5451735544	+919827315972	1BVtsOHoBuzNjr9tkUlj9V7GR97Hc-h8R3x3XxzCILfPXbVQpZFtRq8a7H9xS4wy9NiQjHR2MtE6M9QD3qT31bp5-S9cDeKlEx_gaI8D9dVmDi0A7J5Zhro5Ls3WXzSOFBsceE7LDECdjNU4wkmSHegel96RQ9TepT5O5ieLBBJqjIwMulJcHQ4rgX7DhkRu6PvtEyTI-TYKwkLNR-0Bij5dRBfDmrT04SoWzVJvmmQNeMI1Xd3vGIaRkuG67TI6dzLCVLc9yYNjdy2TcLq87CbjDkQ_hQNL4G7qxgdiAyQE1Dki3ht7yDVGTOK73W4Tc7s9fhcPPdApFcU2oQLzef-bKrn_l-sA=	{}	rule_265425
404962727	+918179508008	1BVtsOHoBu5YrsvwdZ3dmy6u4VOO7VI5vIwQXl-f-jc2nrOgN4uHCVZAF1Ul8JBcgXeEviujMRFEgE1wts-UaE08nGQQvneRw-CERFJAwSkYZqY1RHXXE7O0Nb7g-xhlBernSNvONclsDwl_lu3kpH5XCEyzIzqTR4jmUpLaX7okv5UqS1F8w_OiMzLbHgkOwVN3YK33yvOvoOWKOqzb6G2svJVnaGLWXIpUpFBabaJy1xNHHEd-Eyt98cTTvAhaHaP8V4O4dK1arvoggQXHGdTIHAI8vWSXNdagQyA-f9ts2VMSWYrr2JEnb_lNBI-djvcxJi7oQVxZCwfP08AxpvI9j2Bnz0N0=	{}	rule_265476
6159085054	+919059049094	1BVtsOHoBu4wo_p1pWt4__uqP2kDJniu9ZBPk_5XcuyxjirSLD4v762aMmuD7Oxe7asJcu-lOjMgSrOqtIXJmhqqapx4Vj-sKB78dtNG4X--hfQfpHtbCOB91-x2UtP_vxL7s0mh8R4aoHqcj28Fpx0uqsp_70sdM_zI4UxUNtVHSxMaqkcaVw-cswsugQPnM1SeJCLt3EkUACFet7qiMllLq8pA51aP-8TnI54vWnEV7-fFdbsdZNAHkJuQS2o-db-zLMZ8fyklGvpLXBAG6SPHiW1xmHOxeyoulE0_O4OJk88AuBpIuje2x2uA9RylIIGfmFi3j-j91Ku6YSeLBX6HvvX_Vs58=	{}	rule_265926
8360443949	+17197898162	1AZWarzcBu7G-n1t8joWhUmk8frQamccaJttWSuublAFW295OQxAVZpxi-_SUNfd8kH8QvgZfNobl0HTzxqJ_4dAWX7EdL88vR31QSWSuCTaZ5mSePPpNH43b9exzmzqUDH8tJfv9F9n-tFm5dfEFWytg3Mqla3E1Te48nvq4hzfCY4Z_vX6sXL4opkzyz8n6XHd2R0nxHb4E8hM31M8c1N68oOcHcMrbLgER4fI-DyzKw9W2CErJg3_k2xjZTQCuiXCckfJ0lAismrZdI5hvp2RWQw1n6jKyYnwgajGU1z_Xs6cGe5TV2eOR1VmI5j_uGYwa5FfyNxFmbt-I2LD5poxaJr1wMCE=	{}	rule_299453
6521860950	+855967290531	1BVtsOHoBuxNXCNxoHtbfGFef3zzDqEWQVcrY2MyYTvXuK0EQxeFYh5rKuKb3Q_hV6aYdSMst3KRxnYXxgSIXZWdRAJTsnAn0VwuZTrCILmsEzs2d30T_SiZ-Yd25cbDcQMPOPXqQ57Z2lm1bhDRnaJ2tKCfZSpClWMCFPjlYn6AI17JjudlT4bPYIpPk2Y1MyQw_XKfJadwdIy8SMUlcBGl7D9xX-p21L45sfqWl465mhpqyLK5QoJjVm0r_930ioP311ehpnvAA6v9wlpnIGMRPhKL1uohqBRkZpdzMdfUBnDw6Y0zJGnhFkKB-nsAaLVk4gFBBg3Twcb2MVdxf34vAucfTdT4=	{}	rule_314698
6171495250	+918096484768	1BVtsOHoBu8SB9NBTgQLjb6uHf4RRzft7MDE5TET1OSLKWyiSa_dCwMCk5oIjhFXScb5W77SnxKFMKGhSopxYQT2QRa1zGUQCrG_XKs8iT8CZmWmT7qswQ8pyhe2lrV7MdGBKL1i60K7mj5WPis3uiJz_935t8Sc2hrzzRQgHiwd1cp8xKT5vcQQ8_16mcJSwwWlS2axQJI6b81Wq_MbqVimxQ4DBETee7zCJRMJIH0be72WAn99rftly-pWOUSryWjt9EsFejKx3NqprcERlzTrJSdNrQWRSGzbLSt3gs-vtbCKqSiTu7ZkBdQho_XtgvYOCPW6-uzp5FPK0QOkETwXoBH4lm0U=	{}	rule_343254
5090523346	+919997429918	1BVtsOKUBu04Ohj1M376FAf8QjKQUZVeSnUnfC5SnGUHES5W3zOkdIC2kP1F7CZKyfWpWo7wf0QCoUWLvvugitG25_UAIvKQnoApP7-CLClWPs_GIgivHFtIZy-F-5dzi6Yn-MFmr8OnGqnC6CnV5WcXabwXmciyXeALGksTiz2ahMyWYgIS390cjCiRmPrqA_7GaqezW-P7tkWorL08XfFG2kJz4YGMtoUGIDX_2IHJ9DPC-2LYEXq8YBWnq40SOzYGzUxTiD0VdLOXIEbyyATiAyt3E_AifZzzXo55aVAFgZi046QijiNMXVl-hnJfFyS1QpTm7oyRgaifrjBRNhMvfRQV1Ub0=	{}	rule_403738
6216309591	+255742010761	1BJWap1wBuwPznIpNtbOCNiJ4nDTQnxmBM0QhJ5MEpU3vThu8LXAgNMrgxDScj4qcoE9x1TYig5b4p5NveRBntIrsjp_ArAcD6K_aPxiuW7VRVUChDa2Dn1d4ZrmvHX1vbyNJon3Nn1kJSEtkAHY2AKHGFtlqvws6wF1D_0FjSg4YdN2dJZCB0mMrlm9TWB7Fs5yyrX0FHads5AFEIcpAz3f2N1Z6komcwJ54vSiSomiSnUnvfL7WnR_U-C7SthZasqivlgLyhe7e6LJQ5CeXOhRquHj34i0_0qo4N6WCCRj82yXPiHFnRm2NRrtfyePya4FO-FZ80B-iq2FZdu7UiyJObkMHxig=	{}	rule_414976
8357880060	+8801315301094	1BVtsOKUBu6UeQIWe62DqvQINUHDh3BVcbqdVSimVkD9II7ka0hyvsifYFbsulsrge22LddqP6wTc8kAO-7RDWe0sMwnEG29eBEngzwZOteGqk5jRhqfEgiYH4Y2zb2j4o1TnyT7q57aNNJlimcd6JBKBoFlcgihWb0YaIWu-1CeZO_QbPbWzZNaRTjPUCyJ2m4YOXv8L1v5nPjhUZe1SCAZZx7hBRq6FtSwgEzxyto2aqqdFs18-wYirUnvwdtGwOHMpxFqJf05xS4KHipyLus9q_sgXHRlq2t5ny2lzxjtChWUF9sFE4iT5xBmoq4EXlbvTXpoU3HINKlMWXXejHclIFcuqnDU=	{}	rule_443947
8213596906	+8801826011000	1BVtsOKUBuxCiiQS7xRDEbyPRK53ngZApSkxvm04lcWrpRZaNKw817eU_vkd0cYaAoxRMYX-Zoq3Mc1-hveXBQFXBWKMPy8QO_DEGIs6qqbEM0ixVbp56yLjSJrhnucY8C_PxNDN5nx08nuK6Aneax4YJEN7C7wHl9t-RXrcbrzN39QcEgiPDWgFxScsuJhF8bwOjopsoejU1BLs4iiu4IJO_MklqBNG1FcuJkatJxOgVYzMbhb-tJwdT7pkukYOuego_cLQCVUR1RRAOTS3Kkkr5erOolfAIRV1L8yfrRaXG_SRbvPFLGgxkwbCpDmiopDwe6F08TZ-RM8xdiBzaoUrWYFaJ76w=	{}	rule_444635
5843862754	+8801326657196	1BVtsOKUBu1pZ1bq7za8dOL3XUX63tp2kqRnnZ-MG3Lb5_S-6MxJ8fVEAXswZg7QTNDJeXcoAoWkgdr2o5YF4eZeTUXvVxGNRl4DOjTXDgdrO8oKKQFUU4amrkIAOA3icDhJD4agetSUMwN261vhA6CoR8axgjVlhtEneX2VuzMlm5hP-dpbLvqLXoZLcWjRxBD7hkaGztYGVWwAVA0HD7Zy2Tt6GDYNlxKbGwXiWEYIuHSsZqlZLBKSYmBJavn3jq_fJ7ShnoVHpOtHmFGr07Akc54ibeuf6tIMnJIa7GaHk4thzSVHvTXPPN3U5RPxz7XnV31jBSSb6NwTGcIQ4razQNNM4oZI=	{}	rule_451484
5907554483	+8801316412307	1BVtsOKUBuzzcn97_z4z1LuggUSW0kN9UqEXobJWFr-WXMGn-JqLa52zsdpaoq38gFYSDrFaXsOvrOvpC8QqcGkjaLk1inzMAJj246HcIQObzt82dnWVmIrM_X2-oKVHhXxyDZmMkd45U2O1Wvso9eNVWZv41AY5eCf1ZtSmN5btdE5Uss6ab6vQz9FMWSaKiwi3cr10FXpRBXTRjwdgf0IrK8GHJXxM3iNCafVpHN8NRWxKffzRHEe3s5vU0XJpWZiJRODlCMsqLh07jar2Vya95o-Yq0CHxRF0mzLC20ZjUnnpudl7V6_kzrkrzcMyyIGRUNFVxuFCyxXjs_7rN9zuxo-t640o=	{}	rule_452727
1019557777	+919242412678	1BVtsOHcBu6Tyo5QFGJX4iJE4Hp66cL6QjLdEkOg2VuOXEjf5YQt7obbiAADv3ppYXCo1B2V-Gi8UxTh4Q28X7ne4X_IEb154-pmqQkFhlGHOxREJ0kd4eXphnkEHdPf7Rly1MpN2hAPkfb5I94TnYIkAjDMb9u9dIPcwnsS-NR9b2g66CKwtG4Hb1cHeK2j7sZIz3o5z14sK7qNJXj5i6_f6uP0Pd5L4DJ7Z-8rifgy1_UYU20GdJgs8LD0BGDx1USXWd_RBdDlHTDMb67in--un0coUFr25yTGLh1UvW9VOkDqUaPdhYdZ6By3ji9vXyrXm1blygoKrVS7GQsDhuWarMkmzNic=	{}	rule_212814
8431059443	+917866921241	1BVtsOHcBuwdU4hwr5kHVrQvcIfp-wZcwBY0AuqSKnznaoKgD0c_Fo27rL6EQCNS4sny2-m2ld_675GMshfeluWCgZR3dgU7dFvbBLcN6KpFGO_lMB929YpIBPddEh_-SfVmMyW_GWX83799DDWWj0zWXwYjNvFzuiTlizVgvA4-N9dmXYUos-DynftxGsa3QHBUYVtEaRbYiTPV-QwNQR-TNvFWenfGK17959sfKHEKVQqZz22qqqeA-mC5-tvyK387Glwwq0l0YA6nvDdeBlMBHZAunSyWmtbnUx5qtV2sLhvg9wV6-dD6vobrHXIfg2rsBGEbJYlVD21Lin9DBViCmiLIlx6k=	{}	rule_782064
7300111554	+919083666540	1BVtsOMgBu0z5Ou4sTlk0rbu8ubpAzpKbykI3vMygBkYPN_J7sB9mqov9jEdF3xYqzDLayCgA3lJz7-pBecFNjvxu8qBvLYGGKW4Kckqs1pc2GZeXVO62qM5wjR7KyAQbn1quYBre5rk-khTlqPa4O6Fzq9syXpUCv9WG6yySMJGFerOLawNSwBeH97LqHUICJ7zvU-kcSr3HD-_B1fpc_FGxOBnFlYRJR-SYO2bkGAFvGzSNlqhdaeCo-zIhITUOd1AHDOD46wr7moSuROZQ7-3hZtLxp68vcgR5l9gVQzoaoQC17pqAUUzPsWEAg3PfN8rQmCtcEbojpzuUiNC9Axkn7rxF1a8=	{}	rule_216260
5479267800	+8801746743441	1BVtsOKUBuyrSaFy4ekEsl0kaEXmnI4e2LEjhcAgpqFxCcXppYxSR22m_cYlsCaTZcB7N8Jk7OI3jQ1CECe_iy54WavVbxCh0AQE--0HbauDg7eSeSrd84fYmSz-jNlJurBCc39f9GRmQBKSEa6dzUT5z7yu3MNMkQ2WV-w4LZd9ivnTjAjUIM-QNjhIR0fMQxkO50hqGZa9p8QRBpZH-470CYQp_MlZYcHPzg19f39V4Pv6WbkRQZ9AXNUOj0pVHlRbMWEHA7tgychMB6fvhqqnjhUpRO5tbP5bUzhN0VBkO1hUE8BOEx0iWEIAsd1ke36IwELWhrn3fGSNbCaZCLgaMQ9DpnPE=	{}	rule_528858
7827652929	+8801774586574	1BVtsOKUBu5p0vXp7KFGh6Th0SCu7Xqxi4w1bxCzx8OTuVOrufOcPcpoeevruXMHuTiRYKu1L8HbOoqE6mTBbTP4CzncyKYmSYoTa9d9j8J1I5Q-CmODy3YAal6JXZ3GnVXjIf_ZJur7h4xY4PRFusz7-b_Nj-cRX4j1ohcKH-XRn_qxarOMZecEEYjR2lvPfTgHBwd81MhSvki3WTKHW30bZJ6ve8Jynk0XfZwX5iW4G3-HkAGGho3Lcbhd2qkeAubUToAzr4drFzBqnx_Ro1bLnSuImbwBihu0lh_yqSimSaad0I5tBHjzrfFxQ5MtzsdkqRS09RaJHe27kDBYSXBHumKjA4d4=	{}	rule_525672
6292741991	+15054414851	1AZWarzwBu3oLSbBdJha4SiUjime_vlhArxNlh4lK8obzJzTA4IpNbBlePCAGCA2qtYQHcPndNnP7MEdF9WtwD8HD-4HCi7prxzR2hpU8nRuEtH3BOJqQN0a1nyM4nGrlnUnVkGdhtsQAHBp4e4QE048ta3kmlJuOejXUUquVNk5lsiewpt-uxFSELh3etGmIlHwtEDPk4h7IlbwjBSreDqwL9lScmvG47hoHMchLqnmmb7mKC4bngQhzSR5nBoPjHVcDGr2GLRiJZOZnq2l5JFtaWorGnwV0U5fzCYQGuNMvDJYnADB5nxHzhDvcFcXe_q8M2O24pum6LmNGXtN3_eXBiEcGZKM=	{}	rule_477180
5285734779	+16812491978	1AZWarzwBuwSvZxhDI9amCTzcd9FqVzzzekYgr8otTmEQCCL2ZpjC6e8CktZEO_M5_d_WbcJWlYugSXuhWx97Xk181EjbXndwLeVAhvvY9osVnKpaPUi9S2AMuSyTgXHQRppnone7OyYFG3v54dumO7MxUhJYgiBlsZynYw77xaybTzZX7qKtjpBYvKrYXE8nzQgjoB1kDquf_8nyN-RDGbw8eEBv6k04FiW-4K_eviTHQKmM-q4g86ZZ4SZA936M3xIVSFYpYzp9OiM5f45pk1nDVCTprUs7J_lqJoVbEzKhpLXQo9D-CCf2BKiXR01ZksFOtmM-EziXRcTao7YjermOZt7wd8o=	{}	rule_477746
7441972956	+8801614629438	1BVtsOKUBu1lU36AavJh1MFsW8Xp1Hy2k5rHPwAfwcIN68kBRBYG6t5IKzu3MWH9bzGlj9h9wv9El0HZSWdbneKMWnbciweT3saXD6SdzCb1KeSvJic4CIhz3euuljFwbQc8MGNhHAmVpg4TnyqMHPLrBaQzPIpnrl-kV_iYrOCejKunmrXIpkjTNOKS5AvuCjPlV6qWIuXFOyj3FJGL-dJFkI1rtGr8q3xF-2-cJefGbue99230dzYs9mMSsTbNLU1HtMGWXWTteUhKp32x49nNSvhDiemai87rphMhfEF01PQKJvvW7z_os05AnVqRiyVVy0LnyRs5M3VdBBsJY69JP3xL6yww=	{}	rule_526198
7713662771	+967 737 352 964	1BJWap1wBu41q8MSXFUPqngzM0AWDHPslHu7cigO0Unqqo6uAx76pu1A8RY9AtZkb4y4CnjDdWAILaaLwjDlsmCNoKbzAlAvhxuZRofkrzCdfwyU6V7LuLews94R-6bwv9Yx-LdsJ6Z64BeA1EZnx3cnH21iXoxmF-ldBM5BWGEJPiE-UI306onaFMyxi9PIpdrBC73-I7m4sp4pYBiQ2AQBKCCbsbP1e512nmK-VohgU3AewX51hLCWl_IqWJw0YfJPFmKOb-XJ3uOraiYOK4dPMogbspuCvYVoEv5MErzx_L7jwjxRAPMJMFVEYEC5znf5cs0scNUq-eXd9JWKhcITfBrd8NTk=	{}	rule_479913
8063683486	+919899484714	1BVtsOKUBu0ilRxSjtSSlhoFwO4GY-7o_13_XHkoEe0savDjvJBrmb_G461Ev6jIWacIahRJP77KdOYG2pcx9LfwhYkiLaIqViZX_JD3GX7v7MmNJaEsMHkPutDSSj4-B9UqPpogNjwLNWe9zEDEihIGZxkVRLGv_EqSe5rDT0116FmUcHYrWwdAyhLBXs5bwQBcCaqpbAKlgKprljr3Pcj-V9fHfhI8ssSyj9tBK-ibJYSfSBs5ExS4JhLhWg5nf__D0guRbQcGjwfPx30ZbokNMlsyDixHIp9tJB4RuSkthXqGHfcHfqWvs6FzO_2u4Td4IFR2mhnXeGsjtJNuvI0wTZuFUCRU=	{}	rule_521570
7829152048	+8801795054269	1BVtsOKUBu2tF4TqIm3eD4GW3X-GY4FG23QHPj9hqLUcYJVQhejg2YSVf66byBpeE0_FPWlapv-39N4rxK5nyas9SRnU8qpYeZgcHu2x4r1BZRmsALXzWFYYRLknPKYsP5xxyPgn83h0K3CfB_gTZNI7ti_murg3PBxG92r5goQybiXZkvbrX2YH6E2K7eLqkeuYbo9t4qFcEMskq767NnNBqVFw5rqlHiJz3seITz_U6bvLNyf6m2Xz8GGdr669Y0x6WssPPz_HhYPhTfo-nSsygA4v7ckptyMGhEYRNR0XmJduunCgZ2e9wPS1VS0i2QTQr-Dp6AO58LVEfPdFsYrogdsaXon4=	{}	rule_527237
7428775931	+8801943819728	1BVtsOKUBu4EcYEbBJHtp0eLX-rdz6j58HCJEslzAWeSqyNE5Tx-0e0po6UqXBN4s1CznLfsESWAuozMYd0isUAPMBhwPgQPDwKg_Fkal_S_f7cGN7elqRYjCcBO3Nbo7KGxgvLospJP8gmekxXP7tFrgKjnRHIUzTvNpCcLGc7037jxArH_ffQwzCAiQ8B9WWwNMBB-EJHu1hTAkKBnPJxI_K5KAI1Usce5rYM_26JRPz_83Fn4Y1M5CFuseGUf8w6lhW_wPHCDqHwtCqmmJC9I8Tj6axPjTpraMCdjKn7qlZc5-brrjPD_BZqQlm_BVNcfPc95AxiH2xPNP7hp1qV_xfTSl63I=	{}	rule_527822
7897782049	+13127710726	1AZWarzwBu8WVq2wGh-g4xDTCq7d-TTKz9G-XP7EvAZiAaCV43IOmke2sjh860ngLSpQiXrEQJmB4Djh5-xkdxEsOfQL5sNvalcb1z2J9yRjt4_KRh7ghUHGPmAIA5ydY9yWJPquNVch0BnAyWAYR_aIY_Z5DkE5SCDFoirWHnfIzVeysJwcN5zt56XHyGB38Tpy7oM1lMCFwAXmTL-3oZ_CUZU_l76VrGl0UpmsBqKWbeRM-sjmVJ9XyR5wnOc1mnLnKVNKL4uKJ66itaB3ndmzclp8KUqQtf5JKONNGvnWGzLqIT7GRWJV6yk0o6y2ssYsdUWykS3KAzZH2ufc-kv7vFRwDPro=	{}	rule_584660
7098716789	+996502374787	1ApWapzMBuxZmyWo5fCkHpCx7geSTDfgWD1I2I58VZn-TIevWwmxGiRdNzOxMOiCzs7A7KHlQJ6fVLsFSxwRdOdVqGMyGczfI73uq0RHmditradXoFJysaUeN8DSZShavylkHjuPa1kBmffLaZHx_8Ue-24KvbtrDAqy4jWcgLhI7HcQObbwxhwUXlonTRiEY3a66XzdAtILQGsCik9T1LHSaftao7o30lZ8vjrqT574WO87JdL09tmD4Fx74rb7_KnqZTRXTizH7522DcQWd6mAPBX_WW0iCtC6r3I5wnGSRuCeZWnIDlNHtRgs8Kee8rXdxGxEyqVIJmhbDqaHZYZowBy3on4c=	{}	rule_591291
6640526724	+8801892306967	1BVtsOHoBuzhxqscmUcTRNNuJtumYhKfAZU_vvUJLwYICA_zJSYG-LdWiz9lQg7PGg0p7Xr-i8zKUUdK03EYLYliAVPssd3X9I1jSKEeEdM9XbxG_iHI9ZfZaTtJL56A7Y_8lGpAN0xYANtzKpVmYy61Fv1QXD-PAJ3oYe5nXfEPzHl2v9T6iBZvemEEWNz1U4ZueMRYO7boVTpY5TXoIBdv-JqWGy20Z6_96Jf2nLxTeNCupiSk3ufQqh8vfi55RauHunLrsOmHgGdN3_PlRd3ndZoj0MmM3VVSYRc5WihjQL0MlbTGVGXbpzMPq6x2iMf45b_S1tNtYEAMQUBZn5oSbxE-RjkE=	{}	rule_628749
1916333182	+8801316412307	1BVtsOHoBu7bph2A-bg3IcoG-5Pt_GBK0zcoQX0VHvHm7DBhOouyRJJgh4wcIvzj85fVwgsMDVarBWZyFlVz_gNXY7ri7470TTnOfn3A4eZSElnAmV1819HyZqvVY4f3mFgUZaOBho6RFlCNjhxyCzpSwZR6PfVHaf-aXG-KOog65wr-aDibvGtUdxcVrp1GaTL23Vr4wl9UEqOfKFCxg_rKihA7LMHWc0UJnBTcJAll4mDP0JsNUiaEsIU_Wj1L9GsfkJYrhzkV3LR_4nlaDbgL3jpKvsY7MnBRhlzxxBrYsCLqAimurbZetfi5a3VccRuAt_oGO9fQdaVL-ULOjQ_fSeOebR2Q=	{}	rule_629316
1931035542	+8801620346672	1BVtsOHoBuzBBbZaPmUsStkelNPNaNODDojjCOiANLXsO6rL9_fbcoEmPdashhCFXhZ-i1JXiKHU7-1bfG_ktSdPN_Pbw1d20tlRVGmSSD5MdWonlEBF42HKszSIM92egC5IEJaj6CXG9-H4qnM_QA3Q4bqJ_x_ecfEDf_sEBWIzBpBGvgHb2ficAgUdOiHxTvlvP_-535N8d03dIjYbeHVvPQJGrgdu0raIaPXahLZKnn6o-YM4z0KhFEiAia1FVHslVq1p5m0cDqRfT_egmHi73ba3FmAGE_6khbbty791G8zy93nFJ-s7URZShXIUYxSpGEtso_-LtMnd74xBEHjPECl5csHs=	{}	rule_629578
5920013494	+8801747752098	1BVtsOHoBu3BQmQl2Wm1tsNj3SuzZRtgvuCPaUL007WNWELdW_f5xEukvrnOENjL3kF6DDOXFJBn6yZCuefTrPR-WOO5MJYdhZWbMIIwT56v_EtKgadwjOCpICIhQSJPAc69EyJAyyc5uOx6RVFA4CM9El9YZZwyqzf9IQIT5rHsjq4tZcN8YReEZHW-YUSUcGV48JNC0FWqFjGld-hv5hCOXjcR2f1TNGZZfdHp-pvOEHKWVu6keX2sD9keOzv7Iq8LRPFX7_b1WiNfQfGQ9-cJ1Skmvkrb6dcOT5nI6B5eubOJr8P2ePeTvgo8wHKlvpscaHP6ogUXF0Pee8M-DMvqQQ1TO7Lg=	{}	rule_630475
5747969128	+8801996678177	1BVtsOHoBu5fwxPu5C8L1TDvf3ROy7MrPqYIUaFwtuv5kFvcWOQIeZLAwhIpkX_VLibp8kf0Brf5G-EIYUOLanEdx4t78KshhuBSE4XRdPOwUAwrzNK4Nu2Ju8H9_iNq1XlmtU1SEUawt5n00H3NwpZ-bWKyrA69n0LVs7qX1aIPxe8CYjS9_QCobEboGmGBXpgL2fA-ezPFpZtfJflT-_YFwqnYjKA3myDxpaJ2KQ1UGLEg_Cm2y1RxeIWVz6IUvYJCOO3fNasYAN6HynBxq1bUt0qGibhw0Y7qhb4IP_k1usYIu7jAPcnNnrs1AslEkMAR2tsVY_X-RYoUFmZN8_KHspP_XM1k=	{}	rule_631076
5457458340	+8801810694726	1BVtsOHoBuwUwnHVBowwWXGfBdHz_ZewLOiQAtZz1uE0LaQOpWu8XuQQSgjPALcN1eGteGJs7xCx9u-6aW7PCvdauBcAxv8MSQ9eAFwv60Ful4LZU6aTnXJ5Golh7FCWXIvkOdbhav_R8cmeQm8GUHBX6iwvVHqqtz7cvx97rq6DCaXYVDwD8yb1iZuyRCWvBgeLK-_YH3fIdcq7O7ZU6zSHm8maO_tRTQlWmgE_-JS4qqHEzVWi1FUehAn9a6f6uqXD8CAQJyMwalV7fsx2aZstdPGbB6DoLOislvLzAN6kVyeOhh0VYOrXpWNT4FRqFDhOj-_A3hD0Kyo679m5DOcgqoVCzRjw=	{}	rule_631366
5794338335	+8801956977382	1BVtsOHoBuwJNjknGQBAiH0Gfaf9BBvXfxi7ZLq_RO6oOWWKyn3pIPif0UGBll4qJ5ujeaTBY1JgsNqrTvz0Nw4JiSw5ZolkJABHARa_vj2WDke9MQHGKoH-6vRBgHMa_hxWYZHqQfOiEhEoD_OAt9Bfl9kq5kNhVaFp-3jrm1fHPADrTZfn6hgtZozdfVpDNKguCKuCT2XpSQpC42OUmOxEFrKRkRcDgMsJPBTbJfyUw2NRoQWpJKsWmy_DSQYuDXvcewjY03U94womyPY3vyK-ro4ADXdiyZjEFDG4goBQwuGP2d2vhSE-BcdexoFwd62XvGfh81TrSd8Abx4QKMhLaxH9nMiE=	{}	rule_631776
487621983	+917974307420	1BVtsOIwBu4jNrQ_rLHD8y_XVxkfZO0uV0MovyhSl84zipi-qwngVbevqcc33y9knHh2o8vBXAjjT9K4eZN_FyI8_OXjTjSipXDru2tzRu6uboFQyMR8Sl9qxxQ9vCdepQCHYB3OQHHZZDlhd4pR5E5W0Mm_Lu4AY78X0-R9T4bfSrEG0TJqALxnFXsRtQjHaowjrkAPbxCN_XuWztz_IfSR5oloaRcnJikZLIek9ATtv9-HKvuAklzYvlixt6_KZeWwkVxDpA2boBpdaMp7oZWYcHRBpv4bDUIFXKxU_Hi9EtxjKGhvsmLfe9BbWUNcDn33AH9iC6M4XZubiyJvsAuTZGYZqWq8=	{}	rule_687069
6876318627	+919923232297	1BVtsOHoBu2EAMX1HatzZJ9UMpR5robmtCqQZcR_mSc3L14DXyVnMn4nAz5n4To1ivFwIf4SVD3oVzLtwAOtObx8uzHuS06Aul95I2FNSvkJNS4X0_bqanfYsjM6UQXGhP1x4hYV7CCvI7iGdKQEO8jnqm80WgIuJ3y6BBH4QaCJLx1g7RzCF8HaX-PGy74H8jhU-VWuSx61idbBbwna1_tPrm17zCzo3WjuU89qgylGFbYmL9tu31xyCTxv4dC2CXwdQmEQ8q5KaSNBaVlJorVQr2Bfci2XJBUcJHaP-GN8iGShN1HA5sPyfV0wyPtYBGGRtbbFzJHQHEJp7_d6YmWxLr0eBt2c=	{}	rule_666944
8450125934	+37253638953	1BJWap1wBu0rLZjlj0Rm_lu7TxgvA1iuEnZz4wKcMoPwLhaK_ATT0EagiDpkh9FsMMmr-_R4aFU5K4MMousHOU7ergLzCew3iFKeYp-oOzMaAhB7s4uULu2pMcfs0d0EcLtrPyBaXoOmzD-mA-Mj2ejNXqyBU9Jp5ZE0l03QCUH__HHNmFUMpvQiy6-5b7hH5PFxnwLGK24nPchFk3eCaaSHjHvTXWpd_kmXNjxAXGlyINplovP0AIdtUWscPPSeUlzKDztDZyTJvlxWhDTRgnRE7RQySTG0me00Qf0sTxTtMHIo5Tn_-L2dSsxUgRy_YJCTasHvt0ipUbtmGYF74tsy_9y9IdTQ=	{}	rule_702337
8243249885	+918319389918	1BVtsOIwBu7USC4fA4ljXP3uyxjQ7iD1xinpGt0lWSvpt8qi2bJlftXAk92Bfa7_QtVSChh7joZRrW_jj7rZQ11M5qKKoquUugPmDYaC1jw9v4lHbuxwn2WSkMSyRyy--hc-UICHcD2tcK3u-SSMUcfC9X0HpweEJIvlxhwyBDF1bJgkvVrm48KwQ66ZLuJ5gyqg5OdSBuwshxeN3j6Z7SNLBV_XwmjB4h1U-yko0PQ3tx7XNVWUpLa7ihfBYLXhFKhHIFe7oucOn5895FHbKVAUa-kLEBIEE6E5DuoiDEvr5cpjdkSi_xcPNGOwe1GsF7fJAj_ndR-Ft_MVVa2wjcw-zFPZi9K0=	{}	rule_770114
1884346879	+917241156520	1BVtsOIwBu2CRhoa5DNHFn-CI36o1cH8RXLlBYkMQH_xovsbh4XA_T8fL46PsnzD2w8H1oUY0U9dcEcMitx_BBc-WP9jXDpmOi8H_Jo35FVfTKBQ-b2fn6BP7Lz6Za67853UbzsAQo4SWklwLwy9Gs6T7oHZ-DWL3LjMFRvKZLkPRXqBYRVh82u8zxmvn_Ih-nw421RXjbNU0En4n2YWSeUiZADe2D1I9gkyxYiqz9yKJRAV8xTlMhVGff8Xqgu13-3F_Ew0W3y4dtHdCUcNtaTWrQrbWC2mlpZSm5Pp_5CFEU1SxdMGc6vB36ujAdznXSDGni4hZXsi-KQ5OpRQi-OS0igIQvXA=	{}	default
5227137974	+917211159411	1BVtsOIwBu8CtPXviAbNxHwcUfGnaUWkXEuOt_HIwvlS1QV1azr0SmyB4PI8S6kyNntZqj3fiXdDSoPGXyed-LERxzjK32c2UmhsVE3jlLPYIOGfSKum3WHkfZVpc-eOjgV-QEbNvJ2L1yMRBUCidrjsFZ35AqTYd_9bu_WtuXBzezBJ6k-_qghPwMAETCtSjO9p0NzwLG9QpnTzENJ8sNzh6coHFaKhTxUW4D_pvzZLYe3qzPVf33iZvSPKKehRrJ_dG7tLuIY1jrSy9cwJ9WAegfYDuRqy_1z2fZe-VQL-tLvZktq8dwVIgB6lijjZ21ZRdo4i3BDujg5ycd_0ToVKYNyFXHHg=	{}	rule_851637
7034015842	+919451686211	1BVtsOIwBu3rgpJPJNKiWPNxUKYrSFLtlwLs3bRKPX9IbJKcuDDpKlCBPnF6zqYZltiNzmGOTnJU2u1z8ZifpeuqKVTDoBpfOMTMoogUJNyUGMo55WrXt4kChOOn9SzX-AKweeMUg9wj3SJgmHrjjz5gJibuZuyVAwpbxsimr5mKe5ORdyZDE5xukOruaYWN302JHm-vHxPaGSbj0RL85kD_UEFamMvv7_6g4aJkMsG2ujWAYKki63DMBvxB-StnKzy67k8nNljXpbrcLmSrYePUsNBSN-GqLlyvWFNGMWa984FYhnkV1itS8sv3u3pKoLWS2Fsro9skoIYFzUdDir3ql99MolTQ=	{}	rule_858214
8547072258	+919135847354	1BVtsOIwBu5NtAC_vzTDKnMthCEgGNYHENhIV6wYPRR04JaOijaumZWuE0kPuwPFbmsAyCHbsZnE2FUzJacHW0_l_sVxowwy3PnXGXDayXGku1XM97W0y8Jbhfu7pbQB1NNILboUVIKnQmqXenuJ4YYv-MQxxLxRgVqd5PZc9ML6_Bf3l2rZV10eo4yEtDTjSwylTXepvRoA1fiTPs3CfZrDOZwyDlp_b5L_4Bv1QgctmNzz0IW46wVb_tqg5e4puVhbz04t5ToJrgtkZR3vtG-9HaOYRxuP-rTtI6JbOdM8X8U4V4cEfCIqk2FF1Wuo1TkDsUi6nQvCVptBHcEX66w-caVvPRnI=	{}	rule_865107
8012129273	+447546740692	1BJWap1wBuxXje-I2ihYKHSpXP6NqqwmHvqZsksgsVCETrdEEA6Rp-58j94t9aOGtotuYKr-SCHUhNaTaW0aLTsSZiSwxeFr-0lW4CiwErqEpLwDAidZeNbT1-urGG5r8Chf8VxkjS2UPD4MG7nQil8qOfRF_0Eg97A8TlM6aK7XlvFxogHDq7VnSYsNLE8gXT396skQ-fBq4U50qfOZr5lNQ1gK8O34XAthmPmEGlaiioN6ddlEpdFGgT-VzZtq3rT8SkWTPkMfgbqh9FqqkFg91cNHK5CC0X076zJ2DcAZRpTWPMqibx3vVKhptQNTECuzT2n_gYBY5T-eDnOS88UQ98dzLxmg=	{}	rule_1036761
1612913307	+5522998169836	1AZWarzMBuwidle5teYrQfw6UwM90-fjLfXuKw4QVbC-3ro-yVN9RmNeHV73WJyeAvvbudhgsfVKDRqYcZh39ZM7gMz5mQL6wgxU2PV6VZMgIeSAnRtwD3EdlZoPY6aPhRlCR9qHapZIZPEK5DcnVa896lcGxlK-zBBRzyvT2LZfLfjesq_TezaULCqDHMFcrVJlyLptCiGBK3gSQMvL3coAr6L3uaWNtUQ4ZG0RIzgq0s4tE36I_UmTYXL4w6wpkwn1U2Ulcph9tLj2C773xBbYjYif3YOl862UxG3B3iS2p2hQpzRP9qZcF12eg6cLl_WvQLqigQhanIXJ-q6YXiw4Ghm2areM=	{}	rule_1117143
6396777448	+919351901446	1BVtsOHcBuxot1fB-DgDzGFN_9W2FtL_qKg_9363abjCFkkK-XleLTsTwtXnBAqwcaiI3oVF_zS6Sbn00nki2xG0paWleLUuo8WZoe3VqxpKnCkurmfs9uFwSvdmV2Joy4FQEOmo6aVLASUq1bALx9GRCvVtNaEes2K7uZQNwk4fWFS0ld8ie0G5JCDj_u3bBW_Gvw6nKYElApgnDVEjzaOgbNSPZO6Aq68tPqBPK3H0nFrLxKyaroJ6dPcn5LwLt3zggC2NTHPjP9h4csj4mqCPCwjtVMI1GD29h6U5Wc7VhJIh9QXjD-fjRA6tVkRgFaGi8CRTv0och2uAAg1WARGXLcKK0a5A=	{}	rule_1173123
5604698232	+919913589416	1BVtsOKABu4jt_wbzLrqwdNXPeFPF5QhEXkuobZmHVCYkXj1VoUYpVo6UGysoa33sqV9YfPLBxKmXqzuGpd8w3jQ8-5qz8iz6CRxsvUUZFHnmIvjr5D6w9RgssWjEE4GGJAvBD6-ONey3XSDZpFh4hGmQkBP6_hm-IYg2hIQjDvB_95eBHbPtIcvhd2oqS_t_vRvLAH4ewmBA_te-bLS6oIiFqi984nAe3PMp_BHWAD1p_PAOqCvcW_Ru1tQ5S7mCCMvVgcGZ4kGf9b7SpaLfLDJWn8B4ekeds3q6rtIajWx3ky4k0n4-3ZggjCZyiewTCeVstQFu0n1FfxpJ_N3VGvArVYOS9BU=	{}	rule_35634
8257807182	+919360925228	1BVtsOHUBuzqGVwI0TjlGN7cF84b4_9xKnY2UL6QEQNa2VisUxOCPOITakLCizkxdfTWNubh3rSm1ua3hXrwoQd1g0V56gXhoqhAkfRskaVpBgFDLa1R6WWttp_PD6uV3p6vrpcL_jei9h2kpuBRCxR8V95By1QENBCCTHNZ16q7W3if0SpXBQ_kjeXrsRwQirpdEmdSWbMNUha6-q1muS3G4_wQYHn5axD-1cdB1bjqI6RbuVP3-k6BHq8zB65iy44HbyyFuAWoFTPYvJQsygBnGzltUfMG0O7Q2VxJFXcWCsf6KfwUydgdzh4nVqoxYh8Wre7i9i1dELybooKXr006MKVdhwQQ=	{}	rule_214400
8252877204	+12089021761	1AZWarzgBu7t6o94NbZqPNnuVNz_qW_yLIhjHi7wH5HB9sMOLQyoon3bctj1TiRUxsFyy2Xt54OSKL0qp5jBioqbXjA192M2B9ewQxESe6exZwHLl-dDhsyDzH7iUMdJ83JBEf1o-n6Kl_3LxZk8Rp001mVBX5PB4ExtgecJJayVOdVlycR0LKOJYIQpALT4GI42wP1G6fGsI_2FtM7L85FRSOS2Hrfu6sItmrVyfb6v8f5_d99mFYzMGdJGt5LrRhd1kBoNNQiImZ7kujHTid482nAvgO7yQf4priIUlsjEAq4Cs8rGKUsjDTdvDhT5bYi3SUPFcz3zanSIAfV0Ei_mGBrwudho=	{}	rule_1458612
2061093227	+96179140595	1BJWap1wBuxneIphyhZJJ0Bst4gT-hXEZlCFTKir7e21YOsec9JXcFKrf37fHVQA6EEP3nNmVQidc6MwuCs0dU-q5kyxaDEBeEjBp8AOp5duDEGITv_2MH2gjk6VFnLMN65XRRYZMcMCM0b-QaG1fxsuqku6f1wg6ulub5d_5RQfoeL_IGxItcJIscsTkoUULTVeHp1XDx2KT69gJ6QtSGznyeIfWazgBlwaMQLxSsKc_HOwDjeD9BQ2_y82R7UcCcTXy61LN_pAC4QujpXEEw5g_EdTpQJZIbOjlXA-B6Dk-sedBKMM3ac-daAuzoR-HMAxaEZU7HYyRUuWj0qAHv9Zi9sP6eOM=	{}	rule_1306930
7555800019	+919315317162	1BVtsOKABuyM6NJHxlFYu-p3cWmD62nl8vwq5pdXlFAj4nGPI8wvzr-GEy-758iUvt78FmB-VcyUU2Jwn3i3PGjkNnheeImvFYnhe8SaDLAEdCwqaxPAL6xuF3P0DP_2mACGiN82ImE2R2L-33gkoSVTdb-YqT7Pug_PHrmcF92KYmiHOBKNUWrXWgJUjeBxMyfina4l6pHk0zk9qL6Zo8_vKz-RGL_pj0engXfjLbTWE6SxziPukgFKqdDtkRlXlvkbWJmNlo7RgRMORPeqU8vcJZ_Enva8BZ8q9r_dDMUqMBuxMF4vac1NvWKSR_MX5-E8ojqPYYzElSh7qCTQyo9p9Who1Qa4=	{}	rule_1807764
6729691597	+919369695475	1BVtsOMgBu7DYP7n45GKvHgliMW62MGFUmyBz43oAHHYGMhiTilPapdvjs5urrbMD67sVopAgNImXiHzBp5wv28P4K0EP2dbOYrjryk3VBeb2693_gxRf5NuUTPH1WO-TSmzkwyLl6nsSAoWRcL8EfF7_xX2ay8pRWOUSIcNi5qVv4LrAw2rH9EH9seN7_RF1OntLD5HG2HqF4u_OoxBvjCsO6Cn_HgyqRbbpycYruV8zurYhL-JqUSftwXg2j1u7tggDvcOkT6PRXLtreTerLCNA1jV6RKeQchmS7eXemBYntSTjsNXYC9PXfDaE9FpVJ12QoDXnNIG2KEtTXZ4TmVb_vWiOgTY=	{}	rule_1722126
7656004679	+918905204654	1BVtsOHcBuyomk1ekDSfb1lqC-XO8HH5r-VUZlHaZCc86011KIxHJeNhJvFYh2YDw2WrIzTOwdwsz1f4cQQlJTdCRUYTpVVUlkf3NDOQRaLryePwipJCADD1bqm1c4IbsRH4-ED8aJ6JR3V8vC1AO7avA93OpfQzYndMIP4NyiFWJ6CRLHahDxnICdQcEYBdaIce_mOScUzYWSYD_KpIJC6eYpV7_F3mTw4w7XnheRhm9ecr1eXDXOmDlBdEwaNre0dRITYXD1mgxsw_zes5UpP2wbvkcbbP0vtVqx4cjHPAQyQiO4R27EbcNvxUx6ZD0o82qHViUaMcWMeHleHN7SHJPK12fblo=	{}	rule_1200589
6848720005	+918287870206	1BVtsOMgBu2FpXcxEy0qartwL7JAfyj11-vRh5c7MpBZZDVuZbU03LPzMkPCy5t0caJkQIwYWnB7b9iqFn-qD3Sm-UZ_Al7c3Qzq8ssrUHLm7Sv64DRtIYoSTvP_zIejE960UIDvoLHFFTSJCQ8NuGsCbRUVSrTrmQyjyI4-MGQlBnV-DWnX5MusaxzLOVz0Plg7cBD9LUWqmdxWd961kXxOSnPMBarURZZUs-QKL_Jxh7GljEiQBKdU0qL1CyFKouQngxUjbiCI0dUQxpnPy2skL5rl0mmDkEKyK8UVrwVP8OIfLprWRlkbJgL6PJqfbrDOnu2s7p-Jqo5ep0auHeZTDe5vvM1M=	{}	rule_38211
8377242910	+971545307234	1BJWap1wBu5SBe11K_lwyw4Hi4-GKZRKKLLd-ysINACk_44PLbPrWXFW0iOBl4MnVUmiV1zh4-jAMPQCE_bUWJKz_Z-XSC-NYrgMMnOhHEhBhSRl7Yt4P0_2Csdwm2q46V5sCRNrf2mrkQp5cfwq6yQX9F1FwBbMNpPoeuGhGN07FZe2nPzNBH1YaA6we0R_USXmyJrTi-hrskgbqXl0RJCTUum84wx_1Vfmv3m3CwrNbAI_GIyRRqXjfa3iNrMvFP2y823d9ePQTBGXLiz0av0dMjEwuY5Qj-X4hjDLmbVTqcOeOTbgMyQGWwGSyBK9h_uvGHN3_6tW0rt2VfdEMT9HogVSnHjA=	{}	rule_215385
7885730692	+919326105284	1BVtsOL8Buw2HCvv5JhbI7AInolbQDYuBW5RrzXVIrZ4nlzvg5FyJPtjN9JAmUsBfwI7SHYYyZ7uQTrQzjuQ5aoEYpJZqImDjv9u3E-27DX-wXqc8FpxlWYvQwnn0tIeIMGP9ceJzA4s2OaTl997Tqkk6NsgyMPqn21h89yFlYaCewBpMwd5PaFZ1D_E34PYmsnnyC5QlbcaYopTcndGkhKkfzEMn7yUFfn4JOFvoaCKTUbb4M-GKW7pgLWrvB5bfAaIoXp0urK3y5hryVpAUrV4S6fs8P6wdbSZy03J8q19-q3Myj9X5G5eiOuy_d03Lru-3-xQCWFI1E-WjU7bLfvKNaiwHvtg=	{}	rule_1521283
7619204326	+233 27 047 1539	1BVtsOMgBu2h5ts7Ap9I_mncqbhVIhRjFo-Ougznby1W7kabu7JO1xdintM9VFja7q-AYJNsE6A3I7BTXS2W-IRzooEkvbJWROqx7bkqS7F6Ut7XCicac3sINeulAFPVBnNaoooISMJYvra40o0dUxUepuZVHkxIoGmCjcUGZIuA5Eo7mP4TfI1Xbm6_5JIfN4nhMEAPvrjl0HT8rcmwia0RIdhyTqaqpNFMvVl9jSfThCvqeWzNcgNM5ESgyEBCk-OD7bGm9YAmpnWayQ7XBZRR0YwnbeUI6QU98WAb-XQxXM3sJzj8wO4YgciWVv3xgiZI6Lf5kbtZjxGw8tHA6Bwr9xSJmsMg=	{}	rule_1688614
7792750331	+917735635308	1BVtsOKABu6ppRT_lOMpgwOLUBnaZm0K3ejIKEmVIrs_0dXKw52BuMh8zyl88cEJi9XpnmKC5sQ3zk_bhk44gAqADNkx9NvNMeQd8LHX2c5m8f_5tKIuOmQWJBmcYzIBcxJ3olzyWpRFi97jmHiOGiHl_31DeQGbEoIp2jC7XeHRaGereEy82NRKb6MTaybf6BePz0UGBBl-Ed7IR0vmvs1xS3Mq2uYa8a1U4SXSBTMHTPZnnBMY_wTSL-1U9I7qFz3LJZSoea5-xp7WDgsMakwAhc_7QV7ZETb9OXHWTbcCcqYqJcgfgGtYc-bZAfX685SQ9SXg-kc6ImJmBSV8WvIgADYUvfAk=	{}	rule_30964
7617682298	+919506811959	1BVtsOMgBuwPrXNxFMvZiL8I0YY4gfRO0BavOqPeElG_DEYwnbrL8eKt1F7hq9_kuq6BZOkoIIFYmDIO4NHV_Rc1fRLJU92-knRHNRHgUPvGcT2zRa9AyEfWTAxEpmh1elnfVeU-0Av-C4E9rkuCg6SC6Bd1wAVomjlLfOOiKOq3uhzI0f5dUZedI3YW3V7-tpocQvZxKF8plle97rBVsruRPZiuqUnF9lzIodPPZia_gskhfLOErUwk0qEJ3SeyV1NhbkMHvjP4-6DIUvicAiZPgvBlKUj6IJGycwYIdel6EuhOr5NNMX7kyxLfThYqgOz12eRSjOxwvVB-KELCj33Vg4WyYGPM=	{}	rule_1543974
625596166	+918660232275	1BVtsOMgBu4hRQU_5BD9ZcSmuErY3bSo_CXdrC9xKBOOlF4XQ6KFVwYVlx82rthomMQRIoNTKR2q8pw98sT18j0xyD6cSLjVq9qmAsj5BKQFHrh_9Ry6_sqDlvmX8wfqKD01qwl_guNSS1QfaL8C2CVPW9TCOSeTgtbenjrrIzxe28j5FjSZiTbTxvM5jT1wsA69eyXRYTUfFWnNkauK-8Mv_J5YBM9seQ3_kyO9X7tZoUaxvqb0axCjiGm8C2yXW4m6egAcuXvx4C3HIh26OtnxZVuD4HkheBGWkerIn-ZVQtAuIe_D1pXLAHcHnirb6KmE-p0iiXtVKPRtiqsrVncgkhE-C1sE=	{}	rule_211950
8188198606	+919091627468	1BVtsOMgBu3wvJ4_O0BDyfLx6sMQVxqV0pdprLLDQpyUbq0Z4vmqKmMjeRK5i3R1ydUqx4UNu03nsWQ4FADgi2tSbNcp0hZIxGq8Cr0NLO-WaowIrTKpdwfgg_-AFqThqqQSMh_IzAZe4kK50fhQ1PkzTiODtZbiWVixaVOxoYScpSK6RsFFqBDlr9RYnzENgxfbaZX6rkfiNsgF9z_OG2CViibDBIJuxlptYWXLeyDwpMXqMYgJWSDhIDaGJeobINE_NWk65UHK48CcbAWCTSQcz8VZol65jq78Gq0ZIUcv9Z-LfmpyGR1M47VDU88BNK0T94Dal70sQqImsypeE3JVy48VseW0=	{}	rule_1691815
5112004413	+15204156087	1AZWarzkBuzj1CY01zUO5dRaredz-U7lqATs23kJHwOergMZt8ymuYs1Vj69yQuYIdoi06sukjpdXXTYoil09S8NRcehD8t6ZsKfyM9MRKRDxY0gqa2wSmnsAmptZpfKd_BjmjSVjme0Jzg3NgJVndt3uZ4w2M1yQjjV6zsL1YO0wIzsKC3QWVWBWEcgnrTFHMvT5hK2ccIvZpf8PAKvOLA2K8J2kO2R_bKV6_9YRw31Bo_c7sgodLC5e0TsInaYbmIy4kzsnwO8cymyfuyZXYFjLXhazBgfirrh0SpV8LAEkpPljG6IKvqMyIjgxiyBwbHU_RNTXdmjRzVu_ddOYGiD1xp64JZE=	{}	rule_40037
8586830891	+917850907948	1BVtsOHUBu0HRA3c40_FOwPcZpCovAo6NBnzZOnbZfYl1q8ED97mVeOPQKqW8OxeR5-uDa1bj1NOCmgcvfz11pNdOiUAVw8UNVg1cai6r1cPmczDP2k5oA6zJHdm-Dr1i7Ysh_XU-VpJSeRiDm6KygRL8BguY1sClADHrS6YHXiGleNyTJ0BOrg3cM4KtyPex2q5exWeY1QrbIr2-hetQLgBXNFPGcwWtay4BmzX-K5XtMzq5if8kgnzLQ9h8qH4UXWeEJbd333eMPdtxEnHw8BXVk0-hHJs1-B1uDVcHuq2AwJhx0kTvM-VvXMBQcNkJg9Ou0Nnw_87FJte0kkY0uadAKI7-NnY=	{}	rule_227291
8329946072	+919229975369	1BVtsOHcBuyoaFLIRZYeXdI6xtyb635Q3fm8IDtERG4Xb2HWDwxU9a1weYnyFZ4QuIzNERhn6MAVqx6Vrox57im_BZ4PUZd4aYG1zhUpXo9ORNBCg5KgUmpAFyhhByVZwsImC6Iq2NP0kZdW6E_DwMCt2j97OvtcYyljktTg85lSrpdqz12eV-yXXhNXG_dWE2tHR5SPa-eFnmgzxKtWQBOx0z5DT4xk18QJtiUVjGzNuRyS2caYCR90wui2_6gOEloRw-dIWNuFhsPmhe5xmqONwwYIQQIC66hboT80Ojh7Ir0q84s2I3AeVZT0uQbuFCyXpxfCISZ8clOil_4amGFD3c-hNfxc=	{}	rule_1249508
6617326165	+919491434933	1BVtsOHcBu1i6IunWDUgf8JADzoR0FYYaVPBXgw4N60RHjRKUFXDqBnBrcvCSGtDyGET6rD6rFAJP9WBEDCzIuFtoY_Z0KTfpu0dTaCyi2fK4uxVPbcO_n1oUVDre-MDLsyKOGjVZ48Z03oZuWatteHjIclNIrvp24gi_ISDTlELu5-v2UPV4SsvBiZOeoMpkYpsUFr-7vkTqSRCWcgUvLrSlwQjxWB7TTrAuq6k5IAH7OBWzIlezq6W3ZvIK5rsnEsQ0RkJZZPnpHFUw3JzriNAFUS-UX-QzmQlh3fTJssKeF2PLSOZXDhrV2x13yxwLZg_b8cY8xIYC52Pb3bwv-I7wpGHndQA=	{}	rule_299365
7187275939	+8801319747652	1BVtsOMgBu5O3Yn6wV9jOHwy_YkULYbkJk6ICDNhu2-FHL6nxF6ElrHu8j0TUx_196E3VQZa96XOFBBLcnPIBsQodwpV_ok17faAZvOmxzMpd2D81TuvmHtn8aI_zax79PzK-bjRIjGB1yvOKr8FMHdzTn42x3P7HcAYscLQ1wE4VTXj_JzEEMeV1Ntn01wHqr0Mq6a2er5wzRYEKwq6Tm4zQnrdA_zZxuprmYK1H5jWJSwYvageADw2PT8NQm3ldXzR-_MrGkFM6rh-Vwtl3gTuyQVMgz7YaCYDkohJV_u9OzqgAlVAm19j210awJ2pXeshgqzbopfdRkX1OOFxVfsUMdOAGahI=	{}	default
6594831541	+6281214095667	1BVtsOKABu7yMXQznk5gBmG9eYIZnYFx9zuCZ3JZNbgjS7t-xM_a9fGIXEUnkvhzivgMBPSdh69NYYc9hDvDEU4N2NcicbsFArEEGT64APUJ1Pza1_LGsbYIfz9zUT2-G4Rvlu8aBtqBBf5wHXzVbQiF9eOkUvbh-p_MLnTPU6_Bu-8PBcKHYZ3W995FRxxVKr5UJF8nK-3vv5FfmAfYHUwxKksCsEEe4trA4ONC_jHCYXcIooFPHEh9x7f2QBcYDk8s3iwHGizrwvb-KTq9DANlk-fSfVsAmjQciTuwHn5w9uWlKmwP000PwXSVk5iIOf1X7_KQxOsT_tf004bhM0_iogces6u0=	{}	rule_50544
6421644491	+919795401797	1BVtsOMgBu3csPqjZicN6f8cHWJCRf72FCFu3XjjGlyl9C5CgfVjZZcghmOMRVSN0HGq6zXt3xxqvaLyr8Z5FtbTQOAfeR8UDiVd58ieRq1ClBiU7RVQXqTQL71YmQPWrwzg5kKJIyRMwlM47XGlBLnAGu1E_sE_SfxGRgzr92XiDq5CzUSNXi0047cKIQjlLtD-Ms_sEvLTjlOew1MfKf5VTA24T3g5cLkG8m1vNvvODqoTa5QudRs5c0-qiCDvIDW15o5XKtueqcOdZirrGm6qIvG9JJ3Q6OqagLjeThTtbFe_ruUhyGq52UTn4L2gJ1L1WGQLPRzaUbH74a32pA1UmgHna2H8=	{}	rule_225354
6031182200	+2348140233467	1BJWap1wBuzgDUGQyTyTZ7Z9B1Pu__FxKh8ZwyGsa_qXjWk3VtS-DxHa4Ko-MSrJjVhBZxBBKqVS7bdrvQInVMcxTBxzi_K-QN0wqySnz8p7aRT14wxnYxUce8wFLOUAwf1iW_7BvsQQA1ex4bVoaVDJO2IvDaYQhM1HIQYrKSFF-s0RwUIiPTzDmv-P1DscduRZlsbfF9kcid-6wZFAHJDlR6Obe4wUi7KzlDKKxPfdAUk1bBh0hhZxwxGxd4r8OqGhpFe2IKysB9QsKU7BLtrxhH25rpJclxi1bGa5Q62LVaGCPnsDvHcp8IEyijt8fEaPdHRh-uPQGG3gjKGM80ZmBRrzIsMY=	{}	rule_1292813
7500700453	+998336719712	1ApWapzMBu24a00rd1CC7X1Db8Jfc1wfVv5ZrlpCVKAYal_sy8lwl1QKZG2HxvbYvk9BpnzKCjm6TaY-UPFZ1RIaVDFyOhAWs59T_dwWcANfyImOq0FFARVd2FrMB0uks0Ywy61eX2lKOd-__oFteWXLoE3ri5JYpJNuy7oxvzrkusCvwGRFzrZrzIKpZ64wJhDwBGJoY8tCZ2sKCSmpkWF8JDJcObvb2cgo39fkAuT3H0WUGdR1dC2k26LYvZMlaCCCP3pm_LIahDCuNiLdcW_jbAI_Un_uuErTbJTDzaYep7473-HWuBjAQpYvy1CCETMLvHG2qCIsZ0oYldKf1BxewN3bdTEY=	{}	rule_1384049
5662756526	+998955300019	1ApWapzMBu4H2-MKmPhVRdOWP_5CoRtRsLmVa6D5hES2zNKIzWayLk-3imCpkOIHpcaXo7UJeb_U_l3hpvtBjNXi3jfxnH9Zkuz0K3-FEpK8qDmAhOCHf5l6OSmiSZMx3wBHcsUuQ-fFA2OX2YrHahbiVqw3a4UymUG-UodWV5iUjyz7qw1wnTK0udsHDqH9ihryTrZNozwQdgnhQhiHp9ieVwJmcF6XziQjuhKmRQuGzc2mE6M_tYPy_Js2J94iEEs4EKbUCQSRLSj6Quj-i0q2rrBRg7JCp8AfMhOMYYq9z_tr8ap0M1RlRlNwG33_gDMS3ZlgaJ-angZYCmBeSsdum3kRQ_G0=	{}	rule_1560286
8533537899	+919351290211	1BVtsOMgBu8WhQKbqMsQ6vUX4rfFjI-5O6QqctpOSdyvSsxyqrgpY7FosqHjCAAFtpjOq_1YXwT5fLeUrLlSaEQYNxQUth7H_Z6mJXE9rtks1f7UtTo6XkaqHQXGQRVEAWgTOZ5UizJZKz4inOMBA0FlrNra5FCMYyt_NFSRYzT2WFoaTe9wFY3o7ytk42Lr9SHmBmq-cMer3LUGXVahTk_psmBJfDEZWGfRWSIkJFPUTl3ilogul1zYYEgLby8qpOGugpX7W1DniEllSt0lKQX1lOCK3Yn733yvpxIQ7ewavJ5r7lrPiSfRHAkU006NoxakAVvcyE2g7Fwvcjs4D4jgG1g8li74=	{}	rule_1702735
7515588943	+916371746041	1BVtsOI0BuyX8binJIkgxgrmQRQYTCuUnRL4n3n4FlyoSskrPSthpAsbg06OLsJEhEb7xD4_d_RctNVDg6GooprKee69IQ0FCRiOFr9di20dnBJYgz7NIMFo7O_dg16JKrMWRMfzOekY0HfE5cuJS7Gm7Jk9r18URxf7g5FbwVVw0V37LCzGNkNGb18VmQ2oOEdJYCjl5V6OdPK92BsNTHeqq6JZwYwB-am9zp0RPqzM6aJGPD8Nd1Xc54hJ0xpowhMH_yfvvDLC_1EiNpXJ-9DbF8DxKTwXOl01pfkkxzwZqZfdZRRQ_W7U_RnGR6nQxkmzDLO6BaAHwTtW1FY_HzNlXWmDUE8k=	{}	default
8000547764	+93707920938	1BVtsOHcBu8OFt9YbtrsaCjug7ULleg5zeWxRkF8qV8AuCxVVB-p31tB5acJrq9bsSJunERjEA5KL9f6mwek5hgQZUtKfDJdKNPIK-Drhx9X2UhJElsSgr3JPAPzS-YfCyOXY6l0GVlbbbKS4_Gv5ZJF8SUUZMytVod7JuhI-qaY7sA6agJSWoDVhFBnr8nP3FGu28bMbXn1p5fFPsfOjx7g3vTJynnnehH6_qRCiXJjX6ZrHuV7TVawozWTFJdWki1FBzoYQwiRQGuViOjQAghmGtEuQkE5KTNbIS6e9RG0_-18bHmQlevUwqVq4Lu_GPiqJw8PKr2FSlLlMOd2nLTNv1c29fjU=	{}	rule_1418446
7815565723	+917375856010	1BVtsOMgBu4rOH6GTKo1LRbRHKsx1MqhfKdhcl2RjWs1L-0foJ0Bieunjcybvu_NMm4lcsq_uDzrr-UDAH2MiJk1iHzwfYOM7zQjJkL7R41iq9L1Rk9vin9-Ohk2cEP6bWHzPmYT5twdnq7hFOE-1tE-gzpsbNfCy-bEwRbrEGojLJgI40GAPdeZx4NVpX-At7aVhfIHnVk3KGKM0ofACvHo2QQ5hWVtUR19iwGuN0W72gw1kO48mUYCaUb0P_Tioy__H6h8p2aXTb95LMCcpD3kCU3ZT-LlYRL8op2tzqGMsvO42XwRrXsabV5YxZl8U9JeHGTXa5lWr6JjdOqElvqcsqHuUIMA=	{}	rule_1705886
8005019736	+919250447149	1BVtsOI0Bu6Lq73Ue9eh3RDjsSJEbBADezcSrR0mWb5LbYBv2tpXMxbWwIkJPUm6vlIZSqHmHINgd9YPsQ0q1q9ahoS89G_GAm6CpwuUb_yPSEY_yOerGMVOyoNVK8OwbRYQe_AKpLIcnNleMiUkkXp4Ia9QnJL_hRLozMF5u5IKPUWjC57v-Tf_72sGprwVIkA5khZpZwV0YiFG7T_elHbtYDTGMK9S25XTIh3xaJdrGYtSPmtIiqek8EOgFrCRLKaHLSaxjfEKb-EyXuXDu8dHY97--NjWktbAwwi2q3iSX8ZsjZn9xTsY_xoLheRnqqKcLERDtrdW-zswMMsnDzNieaFj3x5U=	{}	rule_186380
\.


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: telegram_user
--

SELECT pg_catalog.setval('public.messages_id_seq', 1, false);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: telegram_user
--

SELECT pg_catalog.setval('public.payments_id_seq', 353, true);


--
-- Name: admin_users admin_users_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (user_id);


--
-- Name: channel_verification channel_verification_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.channel_verification
    ADD CONSTRAINT channel_verification_pkey PRIMARY KEY (user_id);


--
-- Name: destinations destinations_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.destinations
    ADD CONSTRAINT destinations_pkey PRIMARY KEY (user_id, chat_id, rule_id);


--
-- Name: forwarding_delays forwarding_delays_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.forwarding_delays
    ADD CONSTRAINT forwarding_delays_pkey PRIMARY KEY (user_id, rule_id);


--
-- Name: forwarding_status forwarding_status_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.forwarding_status
    ADD CONSTRAINT forwarding_status_pkey PRIMARY KEY (user_id);


--
-- Name: keyword_filters keyword_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.keyword_filters
    ADD CONSTRAINT keyword_filters_pkey PRIMARY KEY (user_id, rule_id, type);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payments payments_user_id_unique; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_user_id_unique UNIQUE (user_id);


--
-- Name: rules rules_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.rules
    ADD CONSTRAINT rules_pkey PRIMARY KEY (user_id, rule_id);


--
-- Name: sources sources_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.sources
    ADD CONSTRAINT sources_pkey PRIMARY KEY (user_id, chat_id, rule_id);


--
-- Name: subscription_notifications subscription_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.subscription_notifications
    ADD CONSTRAINT subscription_notifications_pkey PRIMARY KEY (user_id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (user_id);


--
-- Name: user_activity user_activity_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_pkey PRIMARY KEY (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: telegram_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO telegram_user;


--
-- PostgreSQL database dump complete
--

