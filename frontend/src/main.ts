import "./assets/main.css";

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
    faGraduationCap,
    faFilter,
    faChartBar,
    faComments,
    faChevronRight,
    faFilePdf,
    faExternalLinkAlt,
    faTimes,
    faChevronDown,
    faUsers,
    faTags,
    faLightbulb,
    faRocket,
    faStar,
    faCheckCircle,
    faTimesCircle,
    faInfoCircle,
} from "@fortawesome/free-solid-svg-icons";

// Add icons to library
library.add(
    faGraduationCap,
    faFilter,
    faChartBar,
    faComments,
    faChevronRight,
    faFilePdf,
    faExternalLinkAlt,
    faTimes,
    faChevronDown,
    faUsers,
    faTags,
    faLightbulb,
    faRocket,
    faStar,
    faCheckCircle,
    faTimesCircle,
    faInfoCircle,
);

const app = createApp(App);

app.component("FontAwesomeIcon", FontAwesomeIcon);
app.use(router);

app.mount("#app");
