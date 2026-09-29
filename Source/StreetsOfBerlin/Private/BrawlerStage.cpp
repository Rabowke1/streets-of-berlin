#include "BrawlerStage.h"

#include "BrawlerAssets.h"
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

void ABrawlerStage::Build()
{
	using namespace Brawler;

	// Himmel mit Fernsehturm (weit hinten, langsame Parallaxe)
	AddLayer(TEXT("BG_Sky"), 2150.f, FloorTopZ + 350.f, -3000.f, 0.15f, SortSky);

	// Fassaden: Unterkante bei FloorTopZ, 560 hoch
	const float WallZ = FloorTopZ + 280.f;
	AddLayer(TEXT("BG_Street_00"), 1024.f, WallZ, -1500.f, 1.f, SortWall);
	AddLayer(TEXT("BG_Street_01"), 3072.f, WallZ, -1500.f, 1.f, SortWall);
	for (int32 i = 0; i < 3; ++i)
	{
		AddLayer(TEXT("BG_UBahn_00"), 5120.f + i * 2048.f, WallZ, -1500.f, 1.f, SortWall);
	}

	// Boden: Oberkante bei FloorTopZ, 420 hoch, 1024 breite Kacheln
	const float FloorZ = FloorTopZ - 210.f;
	for (int32 i = 0; i < 10; ++i)
	{
		const float X = 512.f + i * 1024.f;
		AddLayer(X < 4096.f ? TEXT("BG_FloorStreet") : TEXT("BG_FloorPlatform"), X, FloorZ, -1400.f, 1.f, SortFloor);
	}

	// Vordergrund (vor den Figuren, schnellere Parallaxe)
	const float FgZ = CameraZ;
	for (const float X : { 1500.f, 2900.f, 3800.f })
	{
		AddLayer(TEXT("FG_LampPost"), X, FgZ, 600.f, 1.25f, SortForeground);
	}
	for (const float X : { 4900.f, 6100.f, 7300.f })
	{
		AddLayer(TEXT("FG_Pillar"), X, FgZ, 600.f, 1.25f, SortForeground);
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
