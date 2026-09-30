#include "BrawlerStage.h"

#include "BrawlerAssets.h"
#include "BrawlerStageData.h"
#include "BrawlerTypes.h"
#include "PaperSprite.h"
#include "PaperSpriteComponent.h"
#include "Components/SceneComponent.h"

ABrawlerStage::ABrawlerStage()
{
	PrimaryActorTick.bCanEverTick = false;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void ABrawlerStage::AddLayer(const FString& SpriteName, float BaseX, float CenterZ, float Y, float Parallax, int32 SortPriority)
{
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	UPaperSprite* Spr = Assets ? Assets->GetSprite(TEXT("Backgrounds"), SpriteName) : nullptr;
	if (!Spr)
	{
		return;
	}

	UPaperSpriteComponent* Comp = NewObject<UPaperSpriteComponent>(this);
	Comp->SetupAttachment(GetRootComponent());
	Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Comp->SetGenerateOverlapEvents(false);
	Comp->CastShadow = false;
	Comp->SetSprite(Spr);
	if (UMaterialInterface* Mat = Assets->GetSpriteMaterial())
	{
		Comp->SetMaterial(0, Mat);
	}
	Comp->SetTranslucentSortPriority(SortPriority);
	Comp->RegisterComponent();
	Comp->SetWorldLocation(FVector(BaseX, Y, CenterZ));

	FStageLayer& L = Layers.AddDefaulted_GetRef();
	L.Component = Comp;
	L.BaseX = BaseX;
	L.Parallax = Parallax;
	L.Z = CenterZ;
	L.Y = Y;
}

void ABrawlerStage::Build(const FStageDef& Def)
{
	using namespace Brawler;

	for (FStageLayer& L : Layers)
	{
		if (L.Component)
		{
			L.Component->DestroyComponent();
		}
	}
	Layers.Reset();

	const float HalfW = ScreenWidth * 0.5f;
	for (const FStageArea& Area : Def.Areas)
	{
		// Himmel: Parallaxe 0.15, Basis = Mitte des Kamerabereichs dieses Abschnitts
		if (!Area.Sky.IsEmpty())
		{
			const float Lo = FMath::Max(Area.StartX + HalfW, HalfW);
			const float Hi = FMath::Min(Area.EndX - HalfW, StageEndX - HalfW);
			AddLayer(Area.Sky, (Lo + Hi) * 0.5f, FloorTopZ + 350.f, -3000.f, 0.15f, SortSky);
		}
		// Fassaden: Unterkante bei FloorTopZ, 2048 breit, 560 hoch
		for (int32 i = 0; i < Area.Walls.Num(); ++i)
		{
			AddLayer(Area.Walls[i], Area.StartX + 1024.f + i * 2048.f, FloorTopZ + 280.f, -1500.f, 1.f, SortWall);
		}
		// Boden: 1024 breite Kacheln, Oberkante bei FloorTopZ
		for (float X = Area.StartX; X < Area.EndX; X += 1024.f)
		{
			AddLayer(Area.Floor, X + 512.f, FloorTopZ - 210.f, -1400.f, 1.f, SortFloor);
		}
		// Vordergrund (vor den Figuren, schnellere Parallaxe)
		if (!Area.Foreground.IsEmpty())
		{
			for (const float X : Area.ForegroundX)
			{
				AddLayer(Area.Foreground, X, CameraZ, 600.f, 1.25f, SortForeground);
			}
		}
	}
}

void ABrawlerStage::UpdateParallax(float CameraX)
{
	for (const FStageLayer& L : Layers)
	{
		if (L.Component && L.Parallax != 1.f)
		{
			const float X = CameraX + (L.BaseX - CameraX) * L.Parallax;
			L.Component->SetWorldLocation(FVector(X, L.Y, L.Z));
		}
	}
}
