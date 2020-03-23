import ChartWidget from "../widgets/chart_widget";
import BaseWidget from "../widgets/base_widget";
import ShortcutWidget from "../widgets/shortcut_widget";
import LinksWidget from "../widgets/links_widget";
import OnboardingWidget from "../widgets/onboarding_widget";
import NewWidget from "../widgets/new_widget";

frappe.provide('frappe.widget')

const widget_factory = {
	chart: ChartWidget,
	base: BaseWidget,
	bookmark: ShortcutWidget,
	links: LinksWidget,
	onboarding: OnboardingWidget,
	new: NewWidget
};

export default class WidgetGroup {
	constructor(opts) {
		Object.assign(this, opts);
		this.widgets_list = [];
		this.widgets_dict = {};
		this.make();
	}

	make() {
		this.make_container();
		this.refresh();
	}

	refresh() {
		this.title && this.set_title(this.title);
		this.widgets && this.make_widgets();
		this.options.allow_sorting && this.setup_sortable();
	}

	make_container() {
		const widget_area = $(`<div class="widget-group">
				<div class="widget-group-head">
					<div class="widget-group-title h6 uppercase"></div>
					<div class="widget-group-control h6 text-muted"></div>
				</div>
				<div class="widget-group-body grid-col-${this.columns}">
				</div>
			</div>`);
		this.widget_area = widget_area;
		this.title_area = widget_area.find(".widget-group-title");
		this.control_area = widget_area.find(".widget-group-control");
		this.body = widget_area.find(".widget-group-body");
		widget_area.appendTo(this.container);
	}

	set_title(title) {
		this.title_area[0].innerText = this.title;
	}

	make_widgets() {
		this.body.empty()
		const widget_class = widget_factory[this.type];

		this.widgets.forEach(widget => {
			let widget_object = new widget_class({
				...widget,
				container: this.body,
				on_delete: (name) => this.on_delete(name)
			});
			this.widgets_list.push(widget_object);
			this.widgets_dict[widget.name] = widget_object;
		});
	}

	customize() {
		const options = {
			delete: this.options.allow_delete,
			sort: this.options.allow_sorting
		}

		this.widgets_list.forEach(wid => {
			wid.customize(options);
		})

		this.options.allow_create && new NewWidget({
			container: this.body
		})
	}

	on_delete(name) {
		this.widgets_list = this.widgets_list.filter(wid => name != wid.name)
	}

	setup_sortable() {
		const container = this.body[0];
		this.sortable = new Sortable(container, {
			animation: 150,
			onEnd: () => {
				console.log("Sorting")
			},
			// onChoose: (evt) => this.sortable_config.on_choose(evt, container),
			// onStart: (evt) => this.sortable_config.on_start(evt, container)
		});
	}
}

frappe.widget.WidgetGroup = WidgetGroup;